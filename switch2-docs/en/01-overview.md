# Nintendo Switch 2 – Overview

## Key specs

| Feature | Value | Source |
|---|---|---|
| Launch | June 5, 2025 | ✅ |
| Concept | Hybrid: handheld, tabletop, TV mode via dock | ✅ |
| SoC | Custom NVIDIA Tegra **T239**, package marking `GMLX30-A1` | ✅ (custom NVIDIA) / 🔎 (part name) |
| CPU | 8× ARM Cortex-A78C | 🔎 |
| GPU | NVIDIA Ampere, 1536 CUDA cores, RT and Tensor cores (DLSS) | ✅ (ray tracing, DLSS) / 🔎 (core count) |
| RAM | 12 GB LPDDR5X | ✅ / 🔎 (type) |
| Internal storage | 256 GB UFS 3.1 | ✅ |
| Expansion | microSD Express (up to 2 TB) | ✅ |
| Display | 7.9" LCD, 1920×1080, up to 120 Hz, HDR10, VRR | ✅ |
| TV output | up to 4K/60 Hz, 120 Hz at 1080p/1440p | ✅ |
| Battery | 5220 mAh Li-ion | ✅ |
| Wireless | Wi-Fi 6, Bluetooth | ✅ |
| Ports | 2× USB-C (top + bottom), 3.5 mm jack, game card slot, microSD Express slot | ✅ |
| Operating system | Horizon (successor to the Switch 1 system) | 🔎 |

## Layered architecture

```
┌─────────────────────────────────────────────────────┐
│ Games / apps (EL0, sandboxed)                       │
├─────────────────────────────────────────────────────┤
│ System applets (HOME menu, settings, eShop …)        │
├─────────────────────────────────────────────────────┤
│ System services / sysmodules (fs, sm, hid, nv, …)    │
├─────────────────────────────────────────────────────┤
│ Horizon microkernel (EL1)                           │
├─────────────────────────────────────────────────────┤
│ Secure Monitor / TrustZone (EL3)                    │
├─────────────────────────────────────────────────────┤
│ Boot chain: BootROM → signed stages (PSC, MB1 …)    │
├─────────────────────────────────────────────────────┤
│ Hardware: T239 SoC, LPDDR5X, UFS, PMIC, USB-PD …     │
└─────────────────────────────────────────────────────┘
```

Details:

- Hardware: [02-hardware-soc-memory.md](02-hardware-soc-memory.md), [03-hardware-io-peripherals.md](03-hardware-io-peripherals.md)
- Software: [04-software-os.md](04-software-os.md)
- Security: [05-security.md](05-security.md)

## Key differences from Switch 1

| | Switch 1 (Erista/Mariko) | Switch 2 |
|---|---|---|
| SoC | Tegra X1 / X1+ (T210/T214) | T239 |
| CPU | 4× Cortex-A57 | 8× Cortex-A78C |
| GPU | Maxwell, 256 CUDA cores | Ampere, 1536 CUDA cores |
| RAM | 4 GB LPDDR4(X) | 12 GB LPDDR5X |
| Storage | 32/64 GB eMMC | 256 GB UFS 3.1 |
| Display | 6.2"/7" (OLED), 720p, 60 Hz | 7.9" LCD, 1080p, 120 Hz, HDR |
| Joy-Con | rails | magnetic, mouse sensor |
| Known BootROM bug | Yes (Fusée Gelée, Erista only) | No (as of Oct 2026) |
