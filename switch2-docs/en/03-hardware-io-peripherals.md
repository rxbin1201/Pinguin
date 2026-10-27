# Hardware Part 2: I/O, USB, Power, Wireless, Audio, Dock, Controllers

## 1. Main board chip overview (console)

| Function | Chip | Vendor | Source |
|---|---|---|---|
| SoC | GMLX30-A1 (T239) | NVIDIA | 🔎 iFixit |
| RAM | MT62F768M64D4EK-026 (6 GB LPDDR5X, 2×) | Micron (SK hynix in some revisions) | 🔎 iFixit |
| Storage | HN8T15DEHKX075 (256 GB UFS 3.1) | SK hynix | 🔎 iFixit |
| USB-C / Power Delivery controller | CP10359AT (CCG family) | Infineon (formerly Cypress) | 🔎 iFixit, TechInsights |
| Wi-Fi + Bluetooth | MT3681AEN (2×2 MIMO) | MediaTek | 🔎 iFixit, TechInsights |
| Main PMIC | MAX77851 | Analog Devices / Maxim | ❓ repair community |
| Secondary PMIC / power | DA9092 and others | Renesas (Dialog) | 🔎 TechInsights / ❓ |
| Audio codec | ALC5658 | Realtek | 🔎 iFixit |
| Voice processor (mic, noise suppression) | IG2200 | Intelligo Technology | 🔎 iFixit |
| Game card controller | B2423 | Nintendo (custom) | ❓ iFixit "likely" |

## 2. USB subsystem

### 2.1 Physical ports

- **Bottom USB-C (✅):** dock connection, charging, video output.
- **Top USB-C (✅):** accessories (e.g. the Nintendo Switch 2 Camera) and charging.

### 2.2 How the USB-C port works internally

A USB-C port is made of several cooperating parts:

```
           ┌──────────────────────────────┐
USB-C ─────┤ Infineon PD controller (CCG) │──I²C──► SoC (status, mode)
 CC pins   │ - detects orientation        │
           │ - negotiates USB-PD power    │──────► charger IC / PMIC
           │ - switches alt mode (DP)     │
           └──────────────────────────────┘
USB-C ─────────── high-speed lanes ─────────► SoC: xHCI USB controller
 SS/D+/D-                                     and DisplayPort output
```

1. **CC lines:** the Infineon PD controller detects whether a cable is attached, its orientation, and whether the other side is a power source or sink.
2. **USB Power Delivery:** it negotiates voltage and current with the charger/dock. The official AC adapter is rated at 60 W (🔎).
3. **Alternate mode:** when docked, the controller switches the SuperSpeed lanes to **DisplayPort Alt Mode**. The SoC outputs **DisplayPort**, not HDMI (🔎).
4. **Data:** USB data (accessories, camera, the dock's USB ports) goes through the **xHCI USB host controller** integrated in the T239 (🔎).
5. On Switch 1 this role was filled by a ROHM BM92T36; Switch 2 moved to Infineon (🔎).

### 2.3 Compatibility

Many third-party docks and some chargers do not work, or only partly work, with the Switch 2 (🔎 user reports). The likely reason is a proprietary handshake between console and dock (see section 6).

## 3. Power

| Component | Details |
|---|---|
| Battery | 5220 mAh / approx. 19.7 Wh Li-ion (✅) |
| Battery life | approx. 2–6.5 h depending on the game (✅) |
| PMIC | Generates the many rails for CPU, GPU, RAM and I/O from battery/USB power. The main PMIC is likely a Maxim **MAX77851** (❓), plus Renesas parts (🔎). |
| Charging | via USB-PD (Infineon) plus a charger IC |
| Fuel gauge | measures charge level and battery health (part not publicly confirmed ❓) |

The SoC has its own power-management logic that sets clocks per mode (handheld vs. docked, see CPU/GPU clocks).

## 4. Display & touch

- **7.9" LCD**, 1920×1080, up to **120 Hz**, **HDR10**, **VRR** (variable refresh rate) (✅).
- Capacitive multi-touch (✅).
- Connected via **MIPI DSI** from the SoC's display controller (🔎/❓, standard for Tegra).
- The touch controller is typically attached to the SoC over I²C/SPI (❓, chip not publicly confirmed).

## 5. Wireless & networking

- **MediaTek MT3681** (🔎): combo chip for **Wi-Fi 6 (802.11ax)** 2×2 MIMO and **Bluetooth**.
- Detached Joy-Con 2 and the Pro Controller 2 connect over Bluetooth.
- Local wireless play (multiple consoles) also runs through this chip.
- **NFC** is in the right Joy-Con 2 (amiibo) (✅).
- **LAN:** no port on the console itself. The LAN port is on the dock (see below).

## 6. The dock

The dock is not a passive stand; it is a small computer with its own firmware.

| Function | Chip | Source |
|---|---|---|
| DisplayPort → HDMI converter | **Realtek RTD2175N** (DP 1.4 → HDMI 2.1) | 🔎 ChargerLab, Switchbrew |
| USB hub | **Genesys Logic GL3510** | 🔎 Switchbrew |
| Microcontroller (control, fan, handshake) | **STMicro STM32G0B0** | 🔎 Switchbrew |
| Ethernet (gigabit) | **Realtek RTL8153B** (USB-to-LAN) | 🔎 ChargerLab, Switchbrew |
| USB-C PD controller | Infineon | 🔎 TechInsights |
| Cooling | fan | ✅ |

### Signal path inside the dock

```
Console USB-C ──► PD controller (Infineon) ──► power to console
               ├─► DP Alt Mode ──► RTD2175N ──► HDMI port (TV, up to 4K60 / 1440p120)
               └─► USB 3 ──► GL3510 hub ──┬─► USB-A ports (controllers, accessories)
                                          └─► RTL8153B ──► LAN port (RJ45)
STM32G0B0: fan control, firmware/communication with the console
```

- The LAN chip is a **USB network adapter**, so from the console's point of view Ethernet is a USB device behind the hub.
- Based on datasheet speculation, the RTD2175N could do 4K120, but the console officially outputs at most 4K60 (✅).
- The dock firmware can be updated through the console (🔎).

## 7. Joy-Con 2 & Pro Controller 2

| Feature | Joy-Con 2 | Source |
|---|---|---|
| Attachment | **magnetic** with a release button instead of rails | ✅ |
| Data link when attached | via contact pins on the side | ✅ |
| Data link when detached | Bluetooth | ✅ |
| Mouse function | **optical sensor** on the inner edge (like a PC mouse) | ✅ |
| Rumble | **HD Rumble 2** (linear resonant actuator) | ✅ |
| C button | opens GameChat | ✅ |
| Sensors | gyroscope + accelerometer (IMU) | ✅ |
| NFC | in the right Joy-Con | ✅ |
| Internal MCU / BT chip | not publicly confirmed | ❓ |

On Switch 1, the rail link used UART. Whether Switch 2 uses a similar protocol over the magnetic pins is not officially documented (❓).

**Pro Controller 2 (✅):** additional rear GL/GR buttons, C button, 3.5 mm jack, HD Rumble 2.

## 8. Audio & microphone

- **Realtek ALC5658** codec (🔎): DAC/ADC for speakers, headphones and microphone.
- **Intelligo IG2200** (🔎): voice processor that very likely handles the **AI-assisted noise suppression** of the built-in microphone (the feature is ✅, the chip mapping is 🔎).
- Built-in microphone on the top edge for GameChat (✅).
- Stereo speakers, 3.5 mm jack (✅).

## 9. Camera

The optional **Nintendo Switch 2 Camera** connects over USB-C (top port or dock) (✅). It behaves like a USB camera (UVC-like, ❓ exact protocol). Some third-party USB webcams also work (✅).

## Sources

- [iFixit – Nintendo Switch 2 Chip ID](https://www.ifixit.com/Teardown/Nintendo+Switch+2+Chip+ID/188725)
- [TechInsights teardown (Electronics360)](https://electronics360.globalspec.com/article/23293/techinsights-teardown-nintendo-switch-2)
- [ChargerLab – Teardown of the official dock](https://www.chargerlab.com/teardown-of-nintendo-switch-2-official-charging-dock/)
- [Switchbrew – Switch 2: Dock](https://switchbrew.org/wiki/Switch_2:_Dock)
- [Gameranx – Dock teardown 4K120](https://gameranx.com/updates/id/541945/article/switch-2-dock-teardown-reveals-it-can-support-4k-120hz-and-could-have-had-displayport/)
- [Kasynparts – MAX77851 PMIC (community, less reliable)](https://kasynparts.com/switch-2-max77851s-pmic-repair-guide-wiki-symptoms-diagnostics-and-community-insights/)
- [iFixit Answers – USB-C IC](https://www.ifixit.com/Answers/View/944806/Nintendo+Switch+2+IC+(USB-C)+chip+replacement)
