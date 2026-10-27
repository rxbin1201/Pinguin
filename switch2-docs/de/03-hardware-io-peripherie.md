# Hardware Teil 2: I/O, USB, Stromversorgung, Funk, Audio, Dock, Controller

## 1. Chip-Übersicht Mainboard (Konsole)

| Funktion | Chip | Hersteller | Quelle |
|---|---|---|---|
| SoC | GMLX30-A1 (T239) | NVIDIA | 🔎 iFixit |
| RAM | MT62F768M64D4EK-026 (6 GB LPDDR5X, 2×) | Micron (je nach Revision auch SK hynix) | 🔎 iFixit |
| Speicher | HN8T15DEHKX075 (256 GB UFS 3.1) | SK hynix | 🔎 iFixit |
| USB-C / Power-Delivery-Controller | CP10359AT (CCG-Familie) | Infineon (ehem. Cypress) | 🔎 iFixit, TechInsights |
| Wi-Fi + Bluetooth | MT3681AEN (2×2 MIMO) | MediaTek | 🔎 iFixit, TechInsights |
| Haupt-PMIC | MAX77851 | Analog Devices / Maxim | ❓ Reparatur-Community |
| Neben-PMIC / Power | DA9092 u. a. | Renesas (Dialog) | 🔎 TechInsights / ❓ |
| Audio-Codec | ALC5658 | Realtek | 🔎 iFixit |
| Sprachprozessor (Mikrofon, Geräuschunterdrückung) | IG2200 | Intelligo Technology | 🔎 iFixit |
| Game-Card-Controller | B2423 | Nintendo (custom) | ❓ iFixit „likely“ |

## 2. USB-Subsystem

### 2.1 Physische Anschlüsse

- **USB-C unten (✅):** Dock-Anschluss, Laden, Videoausgabe.
- **USB-C oben (✅):** Zubehör (z. B. die Nintendo-Switch-2-Kamera) und Laden.

### 2.2 Wie der USB-C-Port intern funktioniert

Ein USB-C-Port braucht mehrere Bausteine, die zusammenarbeiten:

```
           ┌──────────────────────────────┐
USB-C ─────┤ Infineon PD-Controller (CCG) │──I²C──► SoC (Status, Modus)
 CC-Pins   │ - erkennt Orientierung       │
           │ - verhandelt USB-PD (Spannung)│──────► Lade-IC / PMIC
           │ - schaltet Alt-Mode (DP)     │
           └──────────────────────────────┘
USB-C ─────────── High-Speed-Leitungen ─────► SoC: xHCI-USB-Controller
 SS/D+/D-                                     und DisplayPort-Ausgang
```

1. **CC-Leitungen:** Der PD-Controller von Infineon erkennt, ob ein Kabel steckt, in welcher Orientierung, und ob das Gegenüber Strom liefert oder braucht.
2. **USB Power Delivery:** Er verhandelt mit dem Netzteil/Dock Spannung und Strom. Das offizielle Netzteil liefert 60 W (🔎).
3. **Alternate Mode:** Im Dock schaltet der Controller die SuperSpeed-Leitungen auf **DisplayPort Alt-Mode** um. Das SoC gibt also **DisplayPort** aus, nicht HDMI (🔎).
4. **Daten:** USB-Daten (Zubehör, Kamera, die USB-Ports am Dock) laufen über den **xHCI-USB-Host-Controller**, der im T239-SoC integriert ist (🔎).
5. Bei der Switch 1 übernahm diese Aufgabe der ROHM BM92T36. Bei Switch 2 wurde auf Infineon gewechselt (🔎).

### 2.3 Kompatibilität

Viele Fremd-Docks und manche Netzteile funktionieren mit der Switch 2 nicht oder nur eingeschränkt (🔎 Nutzerberichte). Der Grund ist vermutlich ein proprietärer Handshake zwischen Konsole und Dock (siehe Abschnitt 6).

## 3. Stromversorgung

| Komponente | Details |
|---|---|
| Akku | 5220 mAh / ca. 19,7 Wh Li-Ion (✅) |
| Laufzeit | ca. 2–6,5 h je nach Spiel (✅) |
| PMIC | Erzeugt aus der Akku-/USB-Spannung die vielen Teilspannungen für CPU, GPU, RAM, I/O. Der Main-PMIC ist vermutlich ein Maxim **MAX77851** (❓), dazu kommen Renesas-Bausteine (🔎). |
| Laden | über USB-PD (Infineon) plus Lade-IC |
| Fuel Gauge | misst Ladestand und Akkugesundheit (Teil nicht öffentlich bestätigt ❓) |

Das SoC hat eine eigene Power-Management-Einheit, die die Takte je nach Modus regelt (Handheld vs. Dock, siehe CPU/GPU-Takte).

## 4. Display & Touch

- **7,9" LCD**, 1920×1080, bis **120 Hz**, **HDR10**, **VRR** (variable Bildwiederholrate) (✅).
- Kapazitiver Multi-Touch (✅).
- Angebunden über **MIPI DSI** vom Display-Controller des SoC (🔎/❓, Standard bei Tegra).
- Der Touch-Controller hängt üblicherweise per I²C/SPI am SoC (❓, Chip nicht öffentlich bestätigt).

## 5. Funk & Netzwerk

- **MediaTek MT3681** (🔎): Kombichip für **Wi-Fi 6 (802.11ax)** 2×2 MIMO und **Bluetooth**.
- Über Bluetooth sind die abgenommenen Joy-Con 2 und der Pro Controller 2 verbunden.
- Lokaler Drahtlosmodus (Spiel mit mehreren Konsolen) läuft ebenfalls über diesen Chip.
- **NFC** sitzt im rechten Joy-Con 2 (amiibo) (✅).
- **LAN:** Kein Port an der Konsole. Der LAN-Port sitzt im Dock (siehe unten).

## 6. Das Dock

Das Dock ist kein „dummer“ Halter, sondern ein kleiner Computer mit eigener Firmware.

| Funktion | Chip | Quelle |
|---|---|---|
| DisplayPort → HDMI-Konverter | **Realtek RTD2175N** (DP 1.4 → HDMI 2.1) | 🔎 ChargerLab, Switchbrew |
| USB-Hub | **Genesys Logic GL3510** | 🔎 Switchbrew |
| Mikrocontroller (Steuerung, Lüfter, Handshake) | **STMicro STM32G0B0** | 🔎 Switchbrew |
| Ethernet (Gigabit) | **Realtek RTL8153B** (USB-zu-LAN) | 🔎 ChargerLab, Switchbrew |
| USB-C-PD-Controller | Infineon | 🔎 TechInsights |
| Kühlung | Lüfter | ✅ |

### Signalweg im Dock

```
Konsole USB-C ──► PD-Controller (Infineon) ──► Strom an Konsole
               ├─► DP Alt-Mode ──► RTD2175N ──► HDMI-Port (TV, bis 4K60 / 1440p120)
               └─► USB 3 ──► GL3510 Hub ──┬─► USB-A-Ports (Controller, Zubehör)
                                          └─► RTL8153B ──► LAN-Port (RJ45)
STM32G0B0: Lüftersteuerung, Firmware/Kommunikation mit der Konsole
```

- Der LAN-Chip ist ein **USB-Netzwerkadapter**. Für die Konsole ist das LAN also ein USB-Gerät hinter dem Hub.
- Der RTD2175N könnte laut Datenblatt-Spekulation auch 4K120. Die Konsole gibt offiziell aber maximal 4K60 aus (✅).
- Die Dock-Firmware kann über die Konsole aktualisiert werden (🔎).

## 7. Joy-Con 2 & Pro Controller 2

| Merkmal | Joy-Con 2 | Quelle |
|---|---|---|
| Befestigung | **magnetisch** mit Entriegelungstaste statt Schiene | ✅ |
| Datenverbindung angedockt | über Kontaktpins an der Seite | ✅ |
| Datenverbindung abgenommen | Bluetooth | ✅ |
| Maus-Funktion | **optischer Sensor** an der Innenseite (wie bei einer PC-Maus) | ✅ |
| Rumble | **HD Rumble 2** (linearer Resonanz-Aktuator) | ✅ |
| C-Taste | öffnet GameChat | ✅ |
| Sensoren | Gyroskop + Beschleunigungssensor (IMU) | ✅ |
| NFC | im rechten Joy-Con | ✅ |
| Interne MCU / BT-Chip | nicht öffentlich bestätigt | ❓ |

Bei der Switch 1 lief die Kommunikation über die Schiene per UART. Ob Switch 2 ein ähnliches Protokoll über die Magnet-Pins nutzt, ist nicht offiziell dokumentiert (❓).

**Pro Controller 2 (✅):** zusätzliche rückseitige GL/GR-Tasten, C-Taste, 3,5-mm-Klinke, HD Rumble 2.

## 8. Audio & Mikrofon

- **Realtek ALC5658** Codec (🔎): DAC/ADC für Lautsprecher, Kopfhörer und Mikrofon.
- **Intelligo IG2200** (🔎): Sprachprozessor, der sehr wahrscheinlich die **KI-gestützte Geräuschunterdrückung** des eingebauten Mikrofons übernimmt (die Funktion selbst ist ✅, die Zuordnung zum Chip 🔎).
- Eingebautes Mikrofon an der Oberseite für GameChat (✅).
- Stereo-Lautsprecher, 3,5-mm-Klinke (✅).

## 9. Kamera

Die optionale **Nintendo-Switch-2-Kamera** wird per USB-C angeschlossen (oberer Port oder Dock) (✅). Sie verhält sich wie eine USB-Kamera (UVC-ähnlich, ❓ genaues Protokoll). Auch einige USB-Webcams von Drittanbietern funktionieren (✅).

## Quellen

- [iFixit – Nintendo Switch 2 Chip ID](https://www.ifixit.com/Teardown/Nintendo+Switch+2+Chip+ID/188725)
- [TechInsights-Teardown (Electronics360)](https://electronics360.globalspec.com/article/23293/techinsights-teardown-nintendo-switch-2)
- [ChargerLab – Teardown des offiziellen Docks](https://www.chargerlab.com/teardown-of-nintendo-switch-2-official-charging-dock/)
- [Switchbrew – Switch 2: Dock](https://switchbrew.org/wiki/Switch_2:_Dock)
- [Gameranx – Dock-Teardown 4K120](https://gameranx.com/updates/id/541945/article/switch-2-dock-teardown-reveals-it-can-support-4k-120hz-and-could-have-had-displayport/)
- [Kasynparts – MAX77851 PMIC (Community, weniger verlässlich)](https://kasynparts.com/switch-2-max77851s-pmic-repair-guide-wiki-symptoms-diagnostics-and-community-insights/)
- [iFixit Answers – USB-C IC](https://www.ifixit.com/Answers/View/944806/Nintendo+Switch+2+IC+(USB-C)+chip+replacement)
