#!/usr/bin/env python3
"""
Wertet einen USBPcap-Mitschnitt (.pcap oder .pcapng) aus, ohne Wireshark/tshark.

Ziel: die tatsaechliche Report-Rate des HID-Endpoints der Switch 2 bestimmen
(deklariert: bInterval 10 = 64 ms, gemessen mit hidapi: ~4 ms).

- Erkennt Geraete-Adressen und, falls die Enumeration mitgeschnitten wurde,
  deren VID:PID aus dem Device-Deskriptor.
- Wertet abgeschlossene Interrupt-IN-Transfers (URB-Completions) aus:
  Anzahl, Rate, Abstaende (min/median/max), Histogramm, Payload-Werte.

Wichtig: USBPcap sieht URBs (Anfragen des Windows-Treibers), nicht den Bus
selbst. NAKs (Geraet hat nichts zu senden) sind unsichtbar. Jede Completion
mit Daten ist aber ein Report, den das Geraet tatsaechlich geliefert hat.

Beispiele:
    python usb_pcap_analyze.py switch.pcapng
    python usb_pcap_analyze.py switch.pcapng --device 5 --endpoint 0x81
"""
import argparse
import statistics
import struct
import sys
from collections import Counter, defaultdict

LINKTYPE_USBPCAP = 249
TRANSFER_TYPES = {0: "isochronous", 1: "interrupt", 2: "control", 3: "bulk", 0xFE: "irp_info"}
INFO_PDO_TO_FDO = 0x01  # gesetzt = Completion (Antwort Richtung Treiber)
STAGE_SETUP, STAGE_COMPLETE = 0, 3

USBD_STATUS = {
    0x00000000: "SUCCESS",
    0x80000300: "INVALID_PARAMETER",
    0xC0000004: "STALL_PID",
    0xC0000005: "DEV_NOT_RESPONDING",
    0xC0000011: "XACT_ERROR",
    0xC0000012: "BABBLE_DETECTED",
    0xC0000030: "ENDPOINT_HALTED",
    0xC0007000: "DEVICE_GONE",
    0xC0010000: "CANCELED",
}

STANDARD_REQUESTS = {
    0x00: "GET_STATUS", 0x01: "CLEAR_FEATURE", 0x03: "SET_FEATURE", 0x05: "SET_ADDRESS",
    0x06: "GET_DESCRIPTOR", 0x07: "SET_DESCRIPTOR", 0x08: "GET_CONFIGURATION",
    0x09: "SET_CONFIGURATION", 0x0A: "GET_INTERFACE", 0x0B: "SET_INTERFACE",
}
HID_CLASS_REQUESTS = {
    0x01: "GET_REPORT", 0x02: "GET_IDLE", 0x03: "GET_PROTOCOL",
    0x09: "SET_REPORT", 0x0A: "SET_IDLE", 0x0B: "SET_PROTOCOL",
}
DESCRIPTOR_TYPES = {
    0x01: "DEVICE", 0x02: "CONFIGURATION", 0x03: "STRING", 0x06: "DEVICE_QUALIFIER",
    0x07: "OTHER_SPEED", 0x0F: "BOS", 0x21: "HID", 0x22: "REPORT",
}


def status_name(code):
    return USBD_STATUS.get(code, f"0x{code:08x}")


def describe_setup(setup):
    bm, req, value, index, length = struct.unpack_from("<BBHHH", setup, 0)
    direction = "IN " if bm & 0x80 else "OUT"
    kind = (bm >> 5) & 0x03
    if kind == 0:
        name = STANDARD_REQUESTS.get(req, f"STD 0x{req:02x}")
    elif kind == 1:
        name = HID_CLASS_REQUESTS.get(req, f"CLASS 0x{req:02x}")
    else:
        name = f"VENDOR 0x{req:02x}"
    detail = f"wValue=0x{value:04x} wIndex=0x{index:04x} wLength={length}"
    if kind == 0 and req == 0x06:
        detail = f"{DESCRIPTOR_TYPES.get(value >> 8, hex(value >> 8))} #{value & 0xFF}, wIndex=0x{index:04x}, wLength={length}"
    elif kind == 1 and req == 0x0A:
        idle = value >> 8
        detail = f"Idle-Rate={idle} ({'nur bei Aenderung' if idle == 0 else f'{idle * 4} ms'}), Report-ID={value & 0xFF}, Interface={index}"
    return f"{direction} {name:<18} {detail}", (kind == 0 and req == 0x06 and value >> 8 == 0x03)


# ---------------------------------------------------------------- Dateiformate

def read_pcap(data):
    magic = data[:4]
    if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):
        endian = "<"
    elif magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
        endian = ">"
    else:
        raise ValueError("kein pcap")
    nano = magic in (b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d")
    linktype = struct.unpack_from(endian + "I", data, 20)[0]
    pos = 24
    while pos + 16 <= len(data):
        sec, frac, incl, _ = struct.unpack_from(endian + "IIII", data, pos)
        pos += 16
        yield linktype, sec + frac / (1e9 if nano else 1e6), data[pos:pos + incl]
        pos += incl


def read_pcapng(data):
    endian = "<"
    interfaces = []  # (linktype, Zeitaufloesung in Sekunden)
    pos = 0
    while pos + 12 <= len(data):
        block_type = struct.unpack_from("<I", data, pos)[0]
        if block_type == 0x0A0D0D0A:  # Section Header Block
            bom = data[pos + 8:pos + 12]
            endian = "<" if bom == b"\x4d\x3c\x2b\x1a" else ">"
            interfaces = []
        block_type, total_len = struct.unpack_from(endian + "II", data, pos)
        body = data[pos + 8:pos + total_len - 4]

        if block_type == 1:  # Interface Description Block
            linktype = struct.unpack_from(endian + "H", body, 0)[0]
            resolution = 1e-6
            opt = 8
            while opt + 4 <= len(body):
                code, length = struct.unpack_from(endian + "HH", body, opt)
                if code == 0:
                    break
                if code == 9 and length >= 1:  # if_tsresol
                    v = body[opt + 4]
                    resolution = 2.0 ** -(v & 0x7F) if v & 0x80 else 10.0 ** -v
                opt += 4 + ((length + 3) & ~3)
            interfaces.append((linktype, resolution))
        elif block_type == 6:  # Enhanced Packet Block
            if_id, ts_hi, ts_lo, caplen, _ = struct.unpack_from(endian + "IIIII", body, 0)
            linktype, resolution = interfaces[if_id]
            yield linktype, ((ts_hi << 32) | ts_lo) * resolution, body[20:20 + caplen]
        pos += total_len


def read_capture(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] == b"\x0a\x0d\x0d\x0a":
        return read_pcapng(data)
    return read_pcap(data)


# ---------------------------------------------------------------- USBPcap

def parse_usbpcap(pkt):
    if len(pkt) < 27:
        return None
    header_len, irp_id, status, function, info, bus, device, endpoint, transfer, data_len = \
        struct.unpack_from("<HQIHBHHBBI", pkt, 0)
    return {
        "stage": pkt[27] if transfer == 2 and header_len >= 28 and len(pkt) > 27 else None,
        "irp": irp_id,
        "status": status,
        "function": function,
        "completion": bool(info & INFO_PDO_TO_FDO),
        "bus": bus,
        "device": device,
        "endpoint": endpoint,
        "transfer": transfer,
        "data": pkt[header_len:header_len + data_len],
    }


# ---------------------------------------------------------------- Auswertung

def percentile(values, p):
    ordered = sorted(values)
    k = (len(ordered) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def histogram(intervals_ms):
    buckets = [(0, 1), (1, 2), (2, 3), (3, 5), (5, 8), (8, 16), (16, 32), (32, 48), (48, 80), (80, 1e9)]
    counts = Counter()
    for v in intervals_ms:
        for lo, hi in buckets:
            if lo <= v < hi:
                counts[(lo, hi)] += 1
                break
    total = len(intervals_ms)
    for lo, hi in buckets:
        n = counts[(lo, hi)]
        if n:
            label = f"{lo:>3}-{hi:<3} ms" if hi < 1e9 else f"{lo:>3}+     ms"
            bar = "#" * max(1, round(40 * n / total))
            print(f"    {label} {n:7d}  {bar}")


def analyze_control(device, controls):
    """Control-Transfers eines Geraets (Setup + Ergebnis) in zeitlicher Reihenfolge ausgeben."""
    print(f"  Control-Requests ({len(controls)}):")
    t0 = controls[0][0] if controls else 0
    for ts, setup, status, data in controls:
        text, is_string = describe_setup(setup)
        result = status_name(status) if status is not None else "keine Antwort"
        if data and not is_string:  # String-Antworten (u. a. Seriennummer) nicht ausgeben
            shown = bytes(data[:96]).hex(" ") + (" ..." if len(data) > 96 else "")
            result += f", {len(data)} Bytes: {shown}"
        elif data:
            result += f", {len(data)} Bytes (String, nicht angezeigt)"
        print(f"    +{(ts - t0) * 1000:8.1f} ms  {text}  -> {result}")


def analyze_interrupt(items):
    ok = [(ts, data) for ts, status, data in items if status == 0 and data]
    errors = Counter(status_name(status) for _, status, _ in items if status != 0)
    print(f"  Interrupt-IN-Completions: {len(items)} (davon mit Daten: {len(ok)})")
    if errors:
        print(f"  Fehlerstatus:           {dict(errors)}")
    if len(ok) < 2:
        print("  Zu wenige Reports fuer eine Zeitauswertung.")
        return None
    duration = ok[-1][0] - ok[0][0]
    intervals_ms = [(b[0] - a[0]) * 1000 for a, b in zip(ok, ok[1:])]
    print(f"  Zeitraum:               {duration:.2f} s")
    print(f"  Rate:                   {(len(ok) - 1) / duration:.1f} Reports/s")
    print(f"  Abstand min/median/max: {min(intervals_ms):.3f} / {statistics.median(intervals_ms):.3f} / {max(intervals_ms):.3f} ms")
    print(f"  Abstand p5/p95:         {percentile(intervals_ms, 0.05):.3f} / {percentile(intervals_ms, 0.95):.3f} ms")
    print("  Histogramm der Abstaende:")
    histogram(intervals_ms)
    payloads = Counter(bytes(d).hex(" ") for _, d in ok)
    print("  Payload-Werte:")
    for value, n in payloads.most_common(10):
        print(f"    {value:<12} {n}x")
    return statistics.median(intervals_ms)


def main():
    parser = argparse.ArgumentParser(description="USBPcap-Mitschnitt auswerten (Report-Rate, Control-Requests).")
    parser.add_argument("capture", help=".pcap oder .pcapng von USBPcap/Wireshark")
    parser.add_argument("--device", type=int, action="append", help="USB-Geraeteadresse(n) (sonst automatisch)")
    parser.add_argument("--endpoint", default="0x81", help="Endpoint (Standard 0x81)")
    parser.add_argument("--vid", default="057e", help="VID fuer die automatische Erkennung (Standard 057e)")
    args = parser.parse_args()
    endpoint = int(args.endpoint, 16)
    want_vid = int(args.vid, 16)

    per_device = defaultdict(Counter)       # device -> Counter(transfer type)
    ids = {}                                # device -> (vid, pid)
    completions = defaultdict(list)         # (device, endpoint) -> [(ts, status, data)]
    pending_setup = {}                      # irp -> (ts, device, setup)
    controls = defaultdict(list)            # device -> [(ts, setup, status, data)]
    skipped_linktypes = Counter()

    for linktype, ts, pkt in read_capture(args.capture):
        if linktype != LINKTYPE_USBPCAP:
            skipped_linktypes[linktype] += 1
            continue
        p = parse_usbpcap(pkt)
        if p is None:
            continue
        per_device[p["device"]][TRANSFER_TYPES.get(p["transfer"], p["transfer"])] += 1
        d = p["data"]

        if p["transfer"] == 2:
            if not p["completion"] and p["stage"] == STAGE_SETUP and len(d) >= 8:
                pending_setup[p["irp"]] = (ts, p["device"], bytes(d[:8]))
            elif p["completion"] and p["stage"] == STAGE_COMPLETE:
                if p["irp"] in pending_setup:
                    ts0, dev, setup = pending_setup.pop(p["irp"])
                    controls[dev].append((ts0, setup, p["status"], d))
                # Device-Deskriptor in einer Control-Antwort -> VID:PID merken
                if len(d) >= 12 and d[0] == 0x12 and d[1] == 0x01:
                    ids[p["device"]] = struct.unpack_from("<HH", d, 8)

        if p["transfer"] == 1 and p["completion"] and p["endpoint"] & 0x80:
            completions[(p["device"], p["endpoint"])].append((ts, p["status"], d))

    # Setups ohne Ergebnis (z. B. Mitschnitt endete vorher)
    for irp, (ts0, dev, setup) in pending_setup.items():
        controls[dev].append((ts0, setup, None, b""))

    if skipped_linktypes:
        print(f"Hinweis: {sum(skipped_linktypes.values())} Pakete mit anderem Linktyp ignoriert {dict(skipped_linktypes)}")

    print("Geraete im Mitschnitt:")
    for dev in sorted(per_device):
        ident = f"{ids[dev][0]:04x}:{ids[dev][1]:04x}" if dev in ids else "VID:PID unbekannt"
        print(f"  Adresse {dev:3d}  {ident:18s} {dict(per_device[dev])}")

    devices = args.device or sorted(dev for dev, (vid, _) in ids.items() if vid == want_vid)
    if not devices:
        candidates = [dev for (dev, ep), items in completions.items()
                      if ep == endpoint and items and all(len(x[2]) == 1 for x in items[:50])]
        if len(candidates) == 1:
            devices = candidates
            print(f"\nEnumeration nicht im Mitschnitt; Geraet {candidates[0]} per Heuristik gewaehlt.")
    if not devices:
        sys.exit("\nGeraet nicht eindeutig erkannt. Bitte --device ADRESSE angeben (siehe Liste oben).")

    medians = []
    for device in devices:
        print(f"\n===== Geraet {device}, Endpoint 0x{endpoint:02x}")
        controls[device].sort(key=lambda c: c[0])
        analyze_control(device, controls[device])
        median = analyze_interrupt(completions.get((device, endpoint), []))
        if median is not None:
            medians.append(median)

    if medians:
        median = statistics.median(medians)
        print("\nEinordnung:")
        if 50 <= median <= 80:
            print("  Abstand entspricht dem deklarierten bInterval (64 ms). Die ~4 ms aus hidapi waren ein Messartefakt.")
        elif median < 10:
            print("  Das Geraet liefert tatsaechlich deutlich oefter Reports als die deklarierten 64 ms.")
            print("  Der Host fragt also haeufiger ab als deklariert, und das Geraet antwortet jedes Mal mit Daten (kein NAK).")
        else:
            print("  Abstand liegt zwischen den Erwartungen. Histogramm genauer ansehen.")


if __name__ == "__main__":
    main()
