#!/usr/bin/env python3
"""
Passiver HID-Logger fuer die Switch 2 (057e:2060).

1. Wartet, bis das HID-Interface der Konsole erscheint.
2. Liest den HID-Report-Deskriptor und schluesselt ihn auf.
3. Liest die Input-Reports mit und loggt jede Aenderung mit Zeitstempel.
4. Eigene Markierungen: Text eintippen + Enter (z. B. "home-menue",
   "schlafmodus") -> landet mit Zeitstempel im Log.
5. Trennt sich die Konsole, wartet das Skript, bis sie wieder erscheint.

Read-only: Es werden nur Deskriptoren und Input-Reports gelesen.
Keine Output- oder Feature-Reports, keine Steuerbefehle.

Installation:
    pip install hidapi

Beispiele:
    python hid_probe.py --out hid1.jsonl
    python hid_probe.py --all              # jeden Report loggen, nicht nur Aenderungen
    python hid_probe.py --show-serial      # Seriennummer nicht kuerzen
"""
import argparse
import json
import queue
import sys
import threading
import time
from datetime import datetime, timezone

import hid

DEFAULT_VID = 0x057E
DEFAULT_PID = 0x2060
READ_TIMEOUT_MS = 100
STATS_INTERVAL_S = 10.0

USAGE_PAGES = {
    0x01: "Generic Desktop", 0x02: "Simulation", 0x06: "Generic Device Controls",
    0x07: "Keyboard", 0x08: "LED", 0x09: "Button", 0x0C: "Consumer",
    0x0D: "Digitizer", 0x0F: "PID", 0x14: "Auxiliary Display", 0x20: "Sensor",
    0x84: "Power Device", 0x85: "Battery System",
}

MAIN_ITEMS = {0x8: "Input", 0x9: "Output", 0xB: "Feature", 0xA: "Collection", 0xC: "End Collection"}
GLOBAL_ITEMS = {
    0x0: "Usage Page", 0x1: "Logical Minimum", 0x2: "Logical Maximum",
    0x3: "Physical Minimum", 0x4: "Physical Maximum", 0x5: "Unit Exponent",
    0x6: "Unit", 0x7: "Report Size", 0x8: "Report ID", 0x9: "Report Count",
    0xA: "Push", 0xB: "Pop",
}
LOCAL_ITEMS = {
    0x0: "Usage", 0x1: "Usage Minimum", 0x2: "Usage Maximum",
    0x3: "Designator Index", 0x4: "Designator Minimum", 0x5: "Designator Maximum",
    0x7: "String Index", 0x8: "String Minimum", 0x9: "String Maximum", 0xA: "Delimiter",
}
COLLECTION_TYPES = {
    0: "Physical", 1: "Application", 2: "Logical", 3: "Report",
    4: "Named Array", 5: "Usage Switch", 6: "Usage Modifier",
}


def usage_page_name(page):
    if page >= 0xFF00:
        return f"Vendor-defined 0x{page:04x}"
    return USAGE_PAGES.get(page, f"0x{page:04x}")


def main_flags(value):
    return ", ".join([
        "Constant" if value & 0x01 else "Data",
        "Variable" if value & 0x02 else "Array",
        "Relative" if value & 0x04 else "Absolute",
    ])


def parse_report_descriptor(data):
    """Zerlegt einen HID-Report-Deskriptor in lesbare Items (Short Items nach HID 1.11)."""
    items = []
    depth = 0
    i = 0
    while i < len(data):
        prefix = data[i]
        if prefix == 0xFE:  # Long Item
            size = data[i + 1] if i + 1 < len(data) else 0
            items.append({"indent": depth, "hex": data[i:i + 3 + size].hex(" "), "text": f"Long Item ({size} Bytes)"})
            i += 3 + size
            continue

        size = (0, 1, 2, 4)[prefix & 0x03]
        item_type = (prefix >> 2) & 0x03
        tag = (prefix >> 4) & 0x0F
        raw = bytes(data[i + 1:i + 1 + size])
        value = int.from_bytes(raw, "little") if raw else 0
        signed = int.from_bytes(raw, "little", signed=True) if raw else 0
        indent = depth

        if item_type == 0:
            name = MAIN_ITEMS.get(tag, f"Main 0x{tag:x}")
            if tag == 0xA:
                text = f"{name} ({COLLECTION_TYPES.get(value, hex(value))})"
                depth += 1
            elif tag == 0xC:
                depth = max(0, depth - 1)
                indent = depth
                text = name
            elif tag in (0x8, 0x9, 0xB):
                text = f"{name} ({main_flags(value)})"
            else:
                text = name
        elif item_type == 1:
            name = GLOBAL_ITEMS.get(tag, f"Global 0x{tag:x}")
            if tag == 0x0:
                text = f"{name} ({usage_page_name(value)})"
            elif tag in (0x1, 0x2, 0x3, 0x4):
                text = f"{name} ({signed})"
            else:
                text = f"{name} ({value})"
        elif item_type == 2:
            name = LOCAL_ITEMS.get(tag, f"Local 0x{tag:x}")
            text = f"{name} (0x{value:02x})"
        else:
            text = f"Reserved (prefix 0x{prefix:02x})"

        items.append({"indent": indent, "hex": bytes([prefix]).hex() + (" " + raw.hex(" ") if raw else ""), "text": text})
        i += 1 + size
    return items


def redact(serial, show):
    if not serial or show:
        return serial
    return serial[:7] + "x" * max(0, len(serial) - 7)


def start_marker_thread():
    """Liest Zeilen von stdin, damit man waehrend der Aufzeichnung Markierungen setzen kann."""
    markers = queue.Queue()

    def reader():
        for line in sys.stdin:
            text = line.strip()
            if text:
                markers.put(text)

    threading.Thread(target=reader, daemon=True).start()
    return markers


class Logger:
    def __init__(self, path):
        self.t0 = time.monotonic()
        self.out = open(path, "a", encoding="utf-8") if path else None

    def rel(self):
        return time.monotonic() - self.t0

    def log(self, event, console, **data):
        t_rel = self.rel()
        print(f"[+{t_rel:9.3f}s] {console}")
        if self.out:
            record = {"time": datetime.now(timezone.utc).isoformat(), "t_rel": round(t_rel, 3), "event": event, **data}
            self.out.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.out.flush()

    def close(self):
        if self.out:
            self.out.close()


def drain_markers(markers, logger):
    while not markers.empty():
        text = markers.get()
        logger.log("marker", f"*** MARKIERUNG: {text}", text=text)


def read_descriptor(dev):
    getter = getattr(dev, "get_report_descriptor", None)
    if getter is None:
        return None, "hidapi zu alt fuer get_report_descriptor (pip install -U hidapi)"
    try:
        return bytes(getter()), None
    except (OSError, ValueError) as e:
        return None, str(e)


def describe_device(info, dev, logger, show_serial):
    logger.log(
        "attach",
        f"+ Geraet gefunden: {info['vendor_id']:04x}:{info['product_id']:04x} "
        f"\"{info.get('product_string')}\" Interface {info.get('interface_number')} "
        f"Usage Page {usage_page_name(info.get('usage_page', 0))}, Usage 0x{info.get('usage', 0):02x}",
        vid_pid=f"{info['vendor_id']:04x}:{info['product_id']:04x}",
        manufacturer=info.get("manufacturer_string"),
        product=info.get("product_string"),
        serial=redact(info.get("serial_number"), show_serial),
        release=f"{info.get('release_number', 0):04x}",
        interface=info.get("interface_number"),
        usage_page=f"0x{info.get('usage_page', 0):04x}",
        usage=f"0x{info.get('usage', 0):04x}",
    )

    descriptor, error = read_descriptor(dev)
    if descriptor is None:
        logger.log("report_descriptor", f"  Report-Deskriptor nicht lesbar: {error}", error=error)
        return

    items = parse_report_descriptor(descriptor)
    logger.log(
        "report_descriptor",
        f"  Report-Deskriptor ({len(descriptor)} Bytes): {descriptor.hex(' ')}",
        raw=descriptor.hex(),
        items=[{"hex": it["hex"], "text": it["text"], "indent": it["indent"]} for it in items],
    )
    for it in items:
        print(f"      {it['hex']:<16} {'  ' * it['indent']}{it['text']}")


def format_report(data):
    raw = bytes(data)
    bits = " ".join(f"{b:08b}" for b in raw)
    return raw.hex(" "), bits


def capture(dev, logger, markers, log_all):
    last = None
    count = 0
    stats_t = time.monotonic()
    while True:
        drain_markers(markers, logger)
        data = dev.read(64, READ_TIMEOUT_MS)  # wirft OSError, wenn das Geraet weg ist
        if data:
            count += 1
            if log_all or data != last:
                hex_str, bits = format_report(data)
                label = "Report" if data == last else "Report geaendert"
                logger.log("report", f"  {label}: {hex_str}  (bits {bits})", data=hex_str, bits=bits, length=len(data))
                last = data
        now = time.monotonic()
        if now - stats_t >= STATS_INTERVAL_S:
            rate = count / (now - stats_t)
            logger.log("stats", f"  {count} Reports in {now - stats_t:.1f}s ({rate:.1f}/s)", reports=count, seconds=round(now - stats_t, 1))
            count = 0
            stats_t = now


def main():
    parser = argparse.ArgumentParser(description="Passiver HID-Logger fuer die Switch 2 (read-only).")
    parser.add_argument("--vid", default=f"{DEFAULT_VID:04x}", help="Vendor-ID hex (Standard 057e)")
    parser.add_argument("--pid", default=f"{DEFAULT_PID:04x}", help="Product-ID hex (Standard 2060)")
    parser.add_argument("--out", help="Ereignisse zusaetzlich als JSON Lines in diese Datei schreiben")
    parser.add_argument("--all", action="store_true", help="Jeden Report loggen, nicht nur Aenderungen")
    parser.add_argument("--show-serial", action="store_true", help="Seriennummer ungekuerzt loggen")
    args = parser.parse_args()

    vid, pid = int(args.vid, 16), int(args.pid, 16)
    logger = Logger(args.out)
    markers = start_marker_thread()
    print(f"Warte auf {vid:04x}:{pid:04x} ... (Text + Enter = Markierung, Strg+C = Ende)")

    try:
        while True:
            drain_markers(markers, logger)
            found = hid.enumerate(vid, pid)
            if not found:
                time.sleep(0.2)
                continue

            info = found[0]
            dev = hid.device()
            try:
                dev.open_path(info["path"])
            except OSError as e:
                logger.log("open_error", f"! Oeffnen fehlgeschlagen: {e}", error=str(e))
                time.sleep(1)
                continue

            try:
                describe_device(info, dev, logger, args.show_serial)
                capture(dev, logger, markers, args.all)
            except OSError as e:
                logger.log("detach", f"- Geraet getrennt ({e})", error=str(e))
            finally:
                dev.close()
    except KeyboardInterrupt:
        print("\nBeendet.")
    finally:
        logger.close()


if __name__ == "__main__":
    main()
