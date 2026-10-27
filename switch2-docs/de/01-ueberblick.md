# Nintendo Switch 2 – Überblick

## Eckdaten

| Merkmal | Wert | Quelle |
|---|---|---|
| Marktstart | 5. Juni 2025 | ✅ |
| Konzept | Hybrid: Handheld, Tabletop, TV-Modus über Dock | ✅ |
| SoC | Custom NVIDIA Tegra **T239**, Package-Aufdruck `GMLX30-A1` | ✅ (custom NVIDIA) / 🔎 (Bezeichnung) |
| CPU | 8× ARM Cortex-A78C | 🔎 |
| GPU | NVIDIA Ampere, 1536 CUDA-Kerne, RT- und Tensor-Kerne (DLSS) | ✅ (Raytracing, DLSS) / 🔎 (Kernzahl) |
| RAM | 12 GB LPDDR5X | ✅ / 🔎 (Typ) |
| Interner Speicher | 256 GB UFS 3.1 | ✅ |
| Erweiterung | microSD Express (bis 2 TB) | ✅ |
| Display | 7,9" LCD, 1920×1080, bis 120 Hz, HDR10, VRR | ✅ |
| TV-Ausgabe | bis 4K/60 Hz, 120 Hz bei 1080p/1440p | ✅ |
| Akku | 5220 mAh, Li-Ion | ✅ |
| Funk | Wi-Fi 6, Bluetooth | ✅ |
| Anschlüsse | 2× USB-C (oben + unten), 3,5-mm-Klinke, Game-Card-Slot, microSD-Express-Slot | ✅ |
| Betriebssystem | Horizon (Nachfolger des Switch-1-Systems) | 🔎 |

## Aufbau in Schichten

```
┌─────────────────────────────────────────────────────┐
│ Spiele / Apps (EL0, sandboxed)                      │
├─────────────────────────────────────────────────────┤
│ System-Applets (HOME-Menü, Einstellungen, eShop …)   │
├─────────────────────────────────────────────────────┤
│ Systemdienste / Sysmodules (fs, sm, hid, nv, …)      │
├─────────────────────────────────────────────────────┤
│ Horizon-Mikrokernel (EL1)                           │
├─────────────────────────────────────────────────────┤
│ Secure Monitor / TrustZone (EL3)                    │
├─────────────────────────────────────────────────────┤
│ Boot-Kette: BootROM → signierte Stufen (PSC, MB1 …) │
├─────────────────────────────────────────────────────┤
│ Hardware: T239-SoC, LPDDR5X, UFS, PMIC, USB-PD …    │
└─────────────────────────────────────────────────────┘
```

Details:

- Hardware: [02-hardware-soc-speicher.md](02-hardware-soc-speicher.md), [03-hardware-io-peripherie.md](03-hardware-io-peripherie.md)
- Software: [04-software-betriebssystem.md](04-software-betriebssystem.md)
- Sicherheit: [05-sicherheit.md](05-sicherheit.md)

## Wichtigste Unterschiede zur Switch 1

| | Switch 1 (Erista/Mariko) | Switch 2 |
|---|---|---|
| SoC | Tegra X1 / X1+ (T210/T214) | T239 |
| CPU | 4× Cortex-A57 | 8× Cortex-A78C |
| GPU | Maxwell, 256 CUDA-Kerne | Ampere, 1536 CUDA-Kerne |
| RAM | 4 GB LPDDR4(X) | 12 GB LPDDR5X |
| Speicher | 32/64 GB eMMC | 256 GB UFS 3.1 |
| Display | 6,2"/7" (OLED), 720p, 60 Hz | 7,9" LCD, 1080p, 120 Hz, HDR |
| Joy-Con | Schienen | magnetisch, Maus-Sensor |
| Bekannte BootROM-Lücke | Ja (Fusée Gelée, nur Erista) | Nein (Stand Okt. 2026) |
