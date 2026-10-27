# USB Observations: Switch 2 connected directly to a PC

Own measurement from **2026-10-27** using [usb_probe.py](../../switch2-tools/usb_probe.py) (passive, GET_DESCRIPTOR only).

## 1. Setup

| | |
|---|---|
| Console | Nintendo Switch 2 (retail) |
| Connection | console's **bottom USB-C port** → PC USB port (direct, no dock) |
| Host | Windows PC, pyusb + libusb |
| Procedure | logger started, then console connected/booted |
| Raw data | `boot1.jsonl` (contains the serial number, do not share publicly) |

> Note: `t_rel` is measured from when the logger started, not from console power-on. The exact delay after power-on was not recorded.

## 2. Summary

- The console enumerates **exactly once** as a USB device (at t = 6.79 s). There are **no intermediate stages** during boot: no second device, no NVIDIA recovery device (`0955:xxxx`), no change of ID.
- The console acts as a **USB device**, with the PC as host.
- Only **one minimal HID interface** is exposed, with a single 1-byte endpoint (console → PC). There is **no** mass storage, MTP or vendor-specific interface.
- The report is always `0x00` and arrives every 4 ms because the Switch rejects `SET_IDLE` (6.5, 6.6).
- A **powered-off** console **boots automatically** when the cable is plugged in and enumerates after a constant ~6.3 s (powered on: ~0.7 s) (6.6, 6.7).

## 3. Device descriptor

| Field | Value | Meaning |
|---|---|---|
| VID:PID | **`057e:2060`** | `057e` = Nintendo, `2060` = Switch 2 product ID in this mode |
| Manufacturer (string) | `Nintendo` | |
| Product (string) | `Nintendo Switch 2` | |
| Serial (string) | `HAE1058xxxxxxx` (truncated) | probably the console serial number (compare with label/settings) |
| bcdUSB | 2.00 | enumerates as a **USB 2.0** device |
| Speed | High Speed (480 Mbit/s) | no SuperSpeed link despite USB-C |
| bcdDevice | 1.00 | device revision |
| Device class | 0x00 | class defined per interface |
| bMaxPacketSize0 | 64 | standard for High Speed |
| Configurations | 1 | |
| BOS descriptor | none | not defined for USB 2.00 (only from 2.01) |

## 4. Configuration, interface, endpoint

```
Configuration 1
  bmAttributes = 0xC0  → self-powered, no remote wakeup
  bMaxPower    = 50    → 50 × 2 mA = 100 mA (draws almost nothing from the bus)
  └─ Interface 0, Alt 0
       Class    0x03 HID
       Subclass 0x00 (not a boot device, i.e. not a BIOS-style keyboard/mouse)
       Protocol 0x00
       └─ Endpoint 0x81
            Direction IN (console → PC)
            Type      interrupt
            MaxPacket 1 byte
            bInterval 10 → at High Speed 2^(10−1) × 125 µs = 64 ms
```

## 5. Interpretation

| Observation | Interpretation | Certainty |
|---|---|---|
| Single HID interface, 1 byte, IN only, polled every 64 ms | Very likely a **minimal placeholder/status interface**. HID needs no driver on Windows, macOS or Linux, so the device shows up cleanly without a "driver not found" error. Section 6 confirms this. | 🔎 supported by measurement |
| No OUT endpoint | The PC **cannot send data to the console** over this interface (except standard control requests on EP0) | ✅ from descriptor |
| No MTP / mass storage interface | **No file access** (e.g. screenshots) over USB in normal operation, at least in this state | ✅ for this state |
| Self-powered, 100 mA | The console powers itself (battery) and requests almost no current via USB data. Charging is handled separately via USB-C/PD. | ✅ from descriptor |
| USB 2.0 instead of 3.x | The SuperSpeed lanes are reserved for **DisplayPort Alt Mode** in the dock; only USB 2.0 is used for data to the PC. | 🔎 plausible |
| No device before the actual enumeration | **No recovery/bootloader USB device** is visible during boot (unlike Switch 1 RCM mode, `0955:7321`) | ✅ for this run |
| Serial number in USB string | The console exposes its serial number to any connected host | ✅ |

## 6. HID analysis (second run)

Measured with [hid_probe.py](../../switch2-tools/hid_probe.py) (hidapi, passive), raw data `hid1.jsonl`.

### 6.1 Report descriptor (26 bytes)

> **Correction:** the first version listed a 24-byte descriptor from `hidapi`. On Windows, hidapi does not read the descriptor raw; it **reconstructs it from the Windows HID driver's data**, which dropped the repeated `05 06`. The USBPcap capture (6.6) shows the real descriptor with **26 bytes**. The meaning is unchanged.

```
05 06            Usage Page (Generic Device Controls)
09 20            Usage (0x20 = Battery Strength)
a1 01            Collection (Application)
09 20              Usage (Battery Strength)
a1 00              Collection (Physical)
05 06                Usage Page (Generic Device Controls)   ← missing in the hidapi version
09 20                Usage (Battery Strength)
15 81                Logical Minimum (-127)
25 7f                Logical Maximum (127)
75 08                Report Size (8)
95 01                Report Count (1)
81 06                Input (Data, Variable, Relative)
c0                 End Collection
c0               End Collection
```

- A single input report: **1 byte, no report ID**. There are **no output or feature reports**, so the PC cannot send anything to the console over HID.
- According to the *HID Usage Tables*, usage `0x06:0x20` is **"Battery Strength"**.
- **This does not add up:** a battery level would be an absolute value (e.g. 0–100 or 0–255), but here the value is declared **relative and signed (−127…127)**. In HID terms a relative value of 0 means "no change", so the OS ignores it.

### 6.2 Timeline

Markers were typed **after** each action (about 4–5 s delay). The mapping follows from the timing pattern.

| t (s) | Event | Interpretation |
|---|---|---|
| 10.5 | enumeration, report `00` | console connected |
| 41.8 | marker `home-menue` | no change |
| 84.7 | marker `spiel-gestartet` (game started) | no change |
| 92.3 | **disconnect** | console enters sleep mode |
| 97.6 | marker `schlafmodus` (sleep) | (typed afterwards) |
| 98.1 | **re-enumeration**, same descriptor | console re-enumerates **while asleep** |
| 105.6 | marker `aufgewacht` (woke up) | **no** disconnect or re-enumeration on wake |
| 115.8 | marker `einstellungen` (settings) | no change |
| 118.9 | **disconnect** | cable unplugged |
| 123.4 | marker `kabel-ab` (cable off) | (typed afterwards) |
| 126.4 | **re-enumeration** | cable plugged in |
| 130.6 | marker `kabel-dran` (cable on) | (typed afterwards) |

### 6.3 Results

| Observation | Details |
|---|---|
| **Byte is always `0x00`** | in every state (HOME menu, game, sleep, settings, after reconnecting) |
| **Report rate ~250/s (every 4 ms)** | a steady 2476–2506 reports per 10 s, also **during sleep mode**. The endpoint descriptor implies 64 ms (~16/s). Confirmed via USBPcap, see 6.5. |
| **Sleep = re-enumeration** | when entering sleep the device disconnects and re-enumerates after ~5.7 s (same ID, same descriptor). It stays active and keeps sending while asleep. |
| **Waking causes no USB event** | the USB device persists unchanged on wake |
| **Cable off/on** | normal disconnect/enumeration, ~7.5 s gap (manual) |

### 6.4 Interpretation

The interface carries **no payload**: the byte is constantly 0, and as a "relative" value 0 means "nothing happened" in HID terms anyway. The most plausible explanation is a **dummy/placeholder HID interface** (❓ hypothesis):

- **HID needs no driver.** Every OS recognizes the device cleanly, without an "unknown device" message.
- **The chosen usage is harmless.** Battery Strength under Generic Device Controls is not bound as a keyboard, mouse or game controller, so the console triggers no input on the PC.
- **Possible purposes** (all ❓): letting the PC detect a data connection, e.g. so power and port role stay stable; a presence signal for Nintendo's own tools (repair/service); or groundwork for future features.

The re-enumeration on sleep suggests the USB device part is re-initialized when the console goes to sleep, and then probably keeps running in a low-power state of the SoC (❓).

### 6.5 USBPcap capture (third run)

Captured with USBPcap on the root hub of the AMD chipset controller (`1022:43EE`), analyzed with [usb_pcap_analyze.py](../../switch2-tools/usb_pcap_analyze.py). The cable was unplugged and replugged once during the capture, so the Switch appears at two addresses:

| Address | Session | Interrupt IN completions | Note |
|---|---|---|---|
| 19 | before unplugging | 1098 in 4.38 s | ends with `CANCELED` (transfer aborted on unplug) and one `INVALID_PARAMETER` |
| 20 | after replugging | ~10,900 | full enumeration captured (24 control packets) |

**Measurements for address 19:**

| Metric | Result |
|---|---|
| Rate | **250.0 reports/s** |
| Interval median | **4.000 ms** |
| Interval p5 / p95 | 3.993 / 4.008 ms |
| Interval min / max | 3.695 / 4.277 ms |
| Payload | 1096× `00`, no other value |

**Result:** the 4 ms is **not a hidapi measurement artifact**. USBPcap sees the driver's completions directly: every request is answered with data, very evenly every 4 ms.

**Interpretation:**
- **Host side:** Windows or the AMD xHCI controller polls the endpoint every 4 ms instead of the 64 ms that `bInterval = 10` implies. Polling frequency is decided by the host alone, so the cause lies in the Windows USB stack or the controller, not in the Switch (❓ exact reason open).
- **Device side:** notably, the Switch answers **every** poll with a report even though the value never changes. A typical HID device NAKs when there is nothing new (idle rate 0), so the driver receives nothing. The Switch apparently always has a report ready. Reason: the Switch rejects `SET_IDLE` (see 6.6).

### 6.6 Enumeration in detail (fourth run)

Procedure: **Switch powered off**, capture started, cable plugged in. Analyzed: address 21.

| t (ms) | Request | Response |
|---|---|---|
| 0.0 | `GET_DESCRIPTOR` Device (18) | OK, `057e:2060`, USB 2.00 |
| 2.7 | `GET_DESCRIPTOR` Configuration (9) | OK, total length 34 bytes |
| 5.8 | `GET_DESCRIPTOR` Configuration (34) | OK, config + interface + HID descriptor + endpoint |
| 8.7 | `SET_CONFIGURATION` 1 | OK |
| 14.1 | **`SET_IDLE` (idle rate 0)** | **STALL** → **rejected** by the Switch |
| 16.0 | `GET_DESCRIPTOR` Report (90 requested) | OK, **26 bytes** |
| 592 / 595 | `GET_DESCRIPTOR` String #2 (product) | OK, 36 bytes = "Nintendo Switch 2" (17 chars) |
| 2578 / 2581 | String #2 again | OK, same response |

**Findings:**

1. **`SET_IDLE` is rejected with a STALL.** With `SET_IDLE` and idle rate 0, Windows asks an HID device to report only on change. The HID spec allows non-boot devices to reject this request. The Switch does so and **therefore reports on every poll**. This explains the device side of the 4 ms observation in 6.5.
2. **Report descriptor:** Windows requests 90 bytes (length from the HID descriptor + a 64-byte buffer, as Windows always does for HID). The Switch returns 26 bytes, which corrects 6.1.
3. **HID descriptor in the configuration:** `09 21 11 01 00 01 …` = HID version **1.11**, country code 0, **one** subordinate descriptor (report). There is no physical descriptor.
4. **No string request for the serial number** and no `SET_ADDRESS` in the capture: these first steps are done by the hub driver below USBPcap and are **not visible** with this method. Windows still has the serial number, see the device instance ID.
5. **Report rate as before:** 247.8/s, median 4.000 ms, values `00` only. 7 of 3237 intervals were above 5 ms (max 72 ms), probably brief pauses in the host's scheduling.
6. **A powered-off Switch turns itself on when the cable is plugged in.** The console was shut down via *hold power button → "Power off"*. When a USB cable to the PC is plugged in, it **boots automatically**. The USB device therefore comes from the **normally booted system**, not from a separate charging or standby mode. Accordingly, device, descriptors, the `SET_IDLE` STALL and the 4 ms reports are **identical** to the powered-on state.
   - > **Correction:** an earlier version suspected a "charging mode with minimal firmware" here. Observing the automatic boot supersedes that.
   - **Privacy:** plugging the powered-off console into an untrusted USB port (e.g. a public charging station) boots it and reveals its **serial number**. Over HID only the same minimal interface is visible (one interface, one IN endpoint, no output/feature reports, `SET_IDLE` rejected).

### 6.7 Time from plug-in to enumeration (fifth run)

Measured with [usb_probe.py](../../switch2-tools/usb_probe.py): Enter was pressed while plugging the cable into the Switch, and the script measures the time until enumeration. 3 runs per state, raw data `timing.jsonl`.

| State | Run 1 | Run 2 | Run 3 | Mean |
|---|---|---|---|---|
| **powered on** | 0.55 s | 0.76 s | 0.72 s | **0.68 s** |
| **powered off** ("Power off", shut down again before each run) | 6.28 s | 6.31 s | 6.32 s | **6.30 s** |

- Descriptors were **identical** in all 6 runs (same ID, same interface, High Speed, same port).
- Measurement uncertainty: reaction time when pressing Enter plus the script's 100 ms polling interval, together about ±0.2 s.

**Result:** when powered off, enumeration takes **about 5.6 s longer**, and **remarkably consistently** (spread only ±0.02 s).

**Interpretation:**
- Plugging in turns the console on (see 6.6, item 6). The **6.3 s** is therefore the time **from power-on to the point during boot at which the USB device function becomes active**. It includes USB PD negotiation, the boot chain (BootROM → signed stages → kernel) and the start of the responsible system service.
- The very small spread indicates a **deterministic boot sequence** up to that point.
- **Before** enumeration at 6.3 s, **no other USB device** appears (no bootloader/recovery device), so the early boot stages expose nothing over USB (🔎 for this setup).
- When powered on, the system is already running; the ~0.7 s is Windows' normal enumeration.
- **Notable parallel:** when entering sleep mode (6.2), the Switch was disconnected for **~5.7 s** before re-enumerating, the same order of magnitude as the 5.6 s here. Possibly the same USB initialization runs in both cases (❓ guess).

**Side observation:** after a **PC reboot** the Switch did not re-enumerate as a USB device on its own; Windows only listed it as not present. It reappeared only after unplugging and replugging the cable.

## 7. Open questions / next steps

1. ~~Read the HID report descriptor~~ → done, see 6.1.
2. ~~Capture input reports~~ → done: value constant `0x00`.
3. ~~Clarify the report rate~~ → done, see 6.5: 4 ms is real.
   ~~Analyze the enumeration control requests~~ → done, see 6.6: `SET_IDLE` is rejected (STALL).
   **Open:** does a Linux host also poll every 4 ms, or is this a Windows/AMD quirk?
   ~~Was the console fully off during run 4?~~ → yes, shut down via "Power off".
   ~~Time from plug-in to enumeration~~ → done, see 6.7: on 0.68 s, off 6.30 s.
   ~~Charging mode → power on~~ → dropped: the console boots automatically when plugged in (6.6).
   **Open:** how long does booting to the HOME menu take compared with the 6.3 s to USB enumeration? That would show how early in the boot process the USB service starts.
4. **Measure timing:** start the logger **first**, then power on and note the moment, to find out at which boot stage enumeration happens.
5. Test the **top USB-C port**: same ID or different behavior?
6. **More states:** console fully off (charging only), reboot, system update, data transfer, album.
7. Connect the **dock to the PC** and compare its hub/LAN chips with the Switchbrew data.
8. Capture **Power Delivery** (CC lines) with a hardware sniffer; this part is invisible to software alone.

## 8. Raw data (excerpt, serial truncated)

The other 12 entries in the log (`event: present`) are the **PC's own** devices (root hubs, internal hubs, Bluetooth, mouse/keyboard, USB stick, etc.) and are unrelated to the Switch.

```json
{"t_rel": 6.793, "event": "attach", "vid_pid": "057e:2060", "bus": 3, "address": 12,
 "device": {"speed": "High (480 Mbit/s)", "bcdUSB": "2.00", "bcdDevice": "1.00",
  "class": "0x00 (per-interface)", "max_packet_ep0": 64, "num_configurations": 1,
  "manufacturer": "Nintendo", "product": "Nintendo Switch 2", "serial": "HAE1058xxxxxxx",
  "configurations": [{"value": 1, "attributes": "0xc0", "max_power_raw": 50,
   "interfaces": [{"number": 0, "alt_setting": 0, "class": "0x03 (HID)",
    "subclass": "0x00", "protocol": "0x00",
    "endpoints": [{"address": "0x81", "direction": "IN", "type": "interrupt",
                   "max_packet": 1, "interval": 10}]}]}],
  "bos": null}}
```
