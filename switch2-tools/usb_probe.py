#!/usr/bin/env python3
"""
Passiver USB-Logger fuer Switch-2-Experimente.

Zeichnet mit Zeitstempel auf, welche USB-Geraete am Host erscheinen und
wieder verschwinden (z. B. waehrend die Konsole bootet), und liest ihre
Standard-Deskriptoren aus: Device, Configuration, Interface, Endpoint,
String und BOS.

Read-only: Es werden ausschliesslich Standard-GET_DESCRIPTOR-Anfragen
gesendet. Kein SET_CONFIGURATION, kein Claim von Interfaces, keine
Vendor-Requests.

Installation:
    pip install pyusb libusb-package

Beispiele:
    python usb_probe.py                       # alle neuen Geraete loggen
    python usb_probe.py --vid 057e --vid 0955 # nur Nintendo / NVIDIA
    python usb_probe.py --out boot1.jsonl     # zusaetzlich als JSON Lines
"""
import argparse
import json
import queue
import sys
import threading
import time
from datetime import datetime, timezone

import usb.core
import usb.util

try:
    import libusb_package  # liefert libusb-1.0 mit (v. a. fuer Windows)
except ImportError:
    libusb_package = None

KNOWN_VENDORS = {
    0x057E: "Nintendo",
    0x0955: "NVIDIA",
    0x04B4: "Cypress/Infineon",
    0x05E3: "Genesys Logic",
    0x0BDA: "Realtek",
    0x0483: "STMicroelectronics",
}

CLASS_NAMES = {
    0x00: "per-interface", 0x01: "Audio", 0x02: "CDC", 0x03: "HID",
    0x05: "Physical", 0x06: "Image", 0x07: "Printer", 0x08: "Mass Storage",
    0x09: "Hub", 0x0A: "CDC-Data", 0x0B: "Smart Card", 0x0E: "Video",
    0x10: "Audio/Video", 0x11: "Billboard", 0xDC: "Diagnostic",
    0xE0: "Wireless", 0xEF: "Misc", 0xFE: "App-specific", 0xFF: "Vendor-specific",
}

BOS_CAP_NAMES = {
    0x01: "Wireless USB", 0x02: "USB 2.0 Extension", 0x03: "SuperSpeed USB",
    0x04: "Container ID", 0x05: "Platform", 0x06: "Power Delivery",
    0x07: "Battery Info", 0x08: "PD Consumer Port", 0x09: "PD Provider Port",
    0x0A: "SuperSpeedPlus", 0x0B: "Precision Time Measurement",
    0x0C: "Wireless USB Ext", 0x0D: "Billboard", 0x0E: "Authentication",
    0x0F: "Billboard Ex", 0x10: "Configuration Summary",
}

SPEED_NAMES = {
    1: "Low (1.5 Mbit/s)", 2: "Full (12 Mbit/s)", 3: "High (480 Mbit/s)",
    4: "Super (5 Gbit/s)", 5: "Super+ (10 Gbit/s)",
}

TRANSFER_TYPES = {0: "control", 1: "isochronous", 2: "bulk", 3: "interrupt"}

DESC_TYPE_BOS = 0x0F
REQ_GET_DESCRIPTOR = 0x06
TIMEOUT_MS = 1000


def get_backend():
    if libusb_package is not None:
        return libusb_package.get_libusb1_backend()
    return None  # pyusb sucht selbst nach einem Backend


def dev_key(dev):
    return (dev.bus, dev.address, dev.idVendor, dev.idProduct)


def vid_pid(dev):
    return f"{dev.idVendor:04x}:{dev.idProduct:04x}"


def read_string(dev, index):
    if not index:
        return None
    try:
        return usb.util.get_string(dev, index)
    except (usb.core.USBError, ValueError, NotImplementedError) as e:
        return f"<nicht lesbar: {e}>"


def read_bos(dev):
    """BOS-Deskriptor lesen (ab USB 2.01). Enthaelt u. a. Billboard-/PD-Capabilities."""
    if dev.bcdUSB < 0x0201:
        return None
    try:
        header = dev.ctrl_transfer(0x80, REQ_GET_DESCRIPTOR, DESC_TYPE_BOS << 8, 0, 5, TIMEOUT_MS)
        total = header[2] | (header[3] << 8)
        raw = bytes(dev.ctrl_transfer(0x80, REQ_GET_DESCRIPTOR, DESC_TYPE_BOS << 8, 0, total, TIMEOUT_MS))
    except (usb.core.USBError, NotImplementedError) as e:
        return {"error": str(e)}

    caps = []
    pos = raw[0]  # Laenge des BOS-Headers
    while pos + 3 <= len(raw):
        length = raw[pos]
        if length < 3:
            break
        cap_type = raw[pos + 2]
        caps.append({
            "type": f"0x{cap_type:02x}",
            "name": BOS_CAP_NAMES.get(cap_type, "unknown"),
            "raw": raw[pos:pos + length].hex(),
        })
        pos += length
    return {"total_length": len(raw), "raw": raw.hex(), "capabilities": caps}


def dump_device(dev):
    info = {
        "vid_pid": vid_pid(dev),
        "vendor_guess": KNOWN_VENDORS.get(dev.idVendor),
        "bus": dev.bus,
        "address": dev.address,
        "port_path": list(dev.port_numbers) if getattr(dev, "port_numbers", None) else None,
        "speed": SPEED_NAMES.get(dev.speed, dev.speed),
        "bcdUSB": f"{dev.bcdUSB >> 8:x}.{dev.bcdUSB & 0xFF:02x}",
        "bcdDevice": f"{dev.bcdDevice >> 8:x}.{dev.bcdDevice & 0xFF:02x}",
        "class": f"0x{dev.bDeviceClass:02x} ({CLASS_NAMES.get(dev.bDeviceClass, '?')})",
        "subclass": f"0x{dev.bDeviceSubClass:02x}",
        "protocol": f"0x{dev.bDeviceProtocol:02x}",
        "max_packet_ep0": dev.bMaxPacketSize0,
        "num_configurations": dev.bNumConfigurations,
        "manufacturer": read_string(dev, dev.iManufacturer),
        "product": read_string(dev, dev.iProduct),
        "serial": read_string(dev, dev.iSerialNumber),
        "configurations": [],
        "bos": read_bos(dev),
    }

    try:
        for cfg in dev:
            cfg_info = {
                "value": cfg.bConfigurationValue,
                "name": read_string(dev, cfg.iConfiguration),
                "attributes": f"0x{cfg.bmAttributes:02x}",
                "max_power_raw": cfg.bMaxPower,
                "interfaces": [],
            }
            for intf in cfg:
                intf_info = {
                    "number": intf.bInterfaceNumber,
                    "alt_setting": intf.bAlternateSetting,
                    "class": f"0x{intf.bInterfaceClass:02x} ({CLASS_NAMES.get(intf.bInterfaceClass, '?')})",
                    "subclass": f"0x{intf.bInterfaceSubClass:02x}",
                    "protocol": f"0x{intf.bInterfaceProtocol:02x}",
                    "name": read_string(dev, intf.iInterface),
                    "endpoints": [
                        {
                            "address": f"0x{ep.bEndpointAddress:02x}",
                            "direction": "IN" if ep.bEndpointAddress & 0x80 else "OUT",
                            "type": TRANSFER_TYPES[ep.bmAttributes & 0x03],
                            "max_packet": ep.wMaxPacketSize,
                            "interval": ep.bInterval,
                        }
                        for ep in intf
                    ],
                }
                cfg_info["interfaces"].append(intf_info)
            info["configurations"].append(cfg_info)
    except (usb.core.USBError, NotImplementedError) as e:
        info["configurations_error"] = str(e)

    return info


def print_summary(event, t_rel, dev, info=None):
    stamp = f"[+{t_rel:8.3f}s]"
    vendor = KNOWN_VENDORS.get(dev[2], "")
    label = f"{dev[2]:04x}:{dev[3]:04x} {vendor}".strip()
    if event == "detach":
        print(f"{stamp} - ENTFERNT  {label} (bus {dev[0]}, addr {dev[1]})")
        return
    print(f"{stamp} + NEU       {label} (bus {dev[0]}, addr {dev[1]})")
    if info:
        print(f"             Produkt: {info['product']!s}  Hersteller: {info['manufacturer']!s}")
        print(f"             USB {info['bcdUSB']}, {info['speed']}, Klasse {info['class']}")
        for cfg in info["configurations"]:
            for intf in cfg["interfaces"]:
                eps = ", ".join(f"{e['address']} {e['type']} {e['direction']}" for e in intf["endpoints"])
                print(f"             IF{intf['number']}.{intf['alt_setting']} {intf['class']}  [{eps}]")
        if info["bos"] and "capabilities" in info["bos"]:
            names = ", ".join(c["name"] for c in info["bos"]["capabilities"])
            print(f"             BOS: {names}")


def main():
    parser = argparse.ArgumentParser(description="Passiver USB-Logger (read-only).")
    parser.add_argument("--vid", action="append", default=[],
                        help="Nur diese Vendor-ID(s) loggen, hex, z. B. 057e (mehrfach moeglich)")
    parser.add_argument("--interval", type=float, default=0.1,
                        help="Abfrageintervall in Sekunden (Standard 0.1)")
    parser.add_argument("--out", help="Ereignisse zusaetzlich als JSON Lines in diese Datei schreiben")
    parser.add_argument("--include-existing", action="store_true",
                        help="Beim Start bereits angeschlossene Geraete ebenfalls voll auslesen")
    args = parser.parse_args()

    vid_filter = {int(v, 16) for v in args.vid}
    backend = get_backend()
    out = open(args.out, "a", encoding="utf-8") if args.out else None
    t0 = time.monotonic()
    last_marker = {"t": None, "text": None}

    # Enter (optional mit Text) = Markierung, z. B. genau beim Einstecken druecken
    markers = queue.Queue()

    def read_markers():
        for line in sys.stdin:
            markers.put((time.monotonic(), line.strip() or "eingesteckt"))

    threading.Thread(target=read_markers, daemon=True).start()

    def wanted(dev):
        return not vid_filter or dev.idVendor in vid_filter

    def write(record):
        if out:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()

    def drain_markers():
        while not markers.empty():
            t_abs, text = markers.get()
            t_rel = t_abs - t0
            last_marker["t"], last_marker["text"] = t_abs, text
            print(f"[+{t_rel:8.3f}s] *** MARKIERUNG: {text}")
            write({"time": datetime.now(timezone.utc).isoformat(), "t_rel": round(t_rel, 3),
                   "event": "marker", "text": text})

    def log(event, key, info=None):
        now = time.monotonic()
        t_rel = now - t0
        print_summary(event, t_rel, key, info)
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "t_rel": round(t_rel, 3),
            "event": event,
            "vid_pid": f"{key[2]:04x}:{key[3]:04x}",
            "bus": key[0],
            "address": key[1],
        }
        if event in ("attach", "detach") and last_marker["t"] is not None:
            delay = now - last_marker["t"]
            record["since_marker_s"] = round(delay, 3)
            record["marker"] = last_marker["text"]
            print(f"             => {delay:.2f} s nach Markierung \"{last_marker['text']}\"")
        if info:
            record["device"] = info
        write(record)

    try:
        known = {dev_key(d): d for d in usb.core.find(find_all=True, backend=backend) if wanted(d)}
    except usb.core.NoBackendError:
        sys.exit("Kein libusb-Backend gefunden. Installiere: pip install libusb-package")

    print(f"Baseline: {len(known)} Geraet(e) bereits angeschlossen. Warte auf Aenderungen ...")
    print("Enter = Markierung setzen (optional mit Text davor), Strg+C = Ende")
    for key, dev in known.items():
        log("present", key, dump_device(dev) if args.include_existing else None)

    try:
        while True:
            drain_markers()
            current ={dev_key(d): d for d in usb.core.find(find_all=True, backend=backend) if wanted(d)}
            for key in current.keys() - known.keys():
                try:
                    info = dump_device(current[key])
                except usb.core.USBError as e:
                    # Geraet kann waehrend des Bootens schon wieder weg sein
                    info = {"error": str(e)}
                log("attach", key, info)
            for key in known.keys() - current.keys():
                log("detach", key)
            known = current
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nBeendet.")
    finally:
        if out:
            out.close()


if __name__ == "__main__":
    main()
