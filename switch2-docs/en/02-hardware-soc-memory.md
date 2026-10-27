# Hardware Part 1: SoC, CPU, GPU, RAM, Storage

## 1. The SoC: NVIDIA T239

The core of the system is a custom NVIDIA chip, internally called **T239**, with the package marking **`GMLX30-A1`** (🔎 iFixit, Tom's Hardware). It integrates the CPU, GPU, memory controller, video engines, display controller, USB controller (xHCI) and security hardware on a single die.

| Property | Value | Source |
|---|---|---|
| Process | Samsung 8 nm (8N) | 🔎 |
| Lineage | Derivative of the Tegra Orin family | 🔎 |
| CPU | 8× Cortex-A78C | 🔎 |
| GPU | Ampere (GA10x generation) | 🔎 |
| Memory interface | 128-bit LPDDR5X | 🔎 |
| Special blocks | File Decompression Engine (FDE), NVENC/NVDEC, display controller | 🔎 |

### 1.1 CPU

- **8 ARM Cortex-A78C cores** (ARMv8.2-A, 64-bit). The "C" variant targets laptops and embedded designs and allows up to 8 big cores in one cluster with a shared L3 cache.
- **Split (🔎, developer leaks):** 6 cores for games, 2 for the OS and background services.
- **Clocks (🔎, Digital Foundry / leaked documents):** about 998 MHz for games in both handheld and docked mode, optionally up to about 1.1 GHz. Higher system clocks (up to ~1.7 GHz) have been documented, e.g. during loading.
- No big.LITTLE: all cores are identical, which makes scheduling simpler for game developers.

### 1.2 GPU

- **Architecture:** NVIDIA Ampere (same generation as the RTX 30 series).
- **Configuration (🔎):** 12 Streaming Multiprocessors (SMs) = **1536 CUDA cores**, 48 Tensor cores, 12 RT cores.
- **Clocks and performance (🔎):**

| Mode | GPU clock | FP32 throughput (approx.) |
|---|---|---|
| Handheld | ~561 MHz | ~1.7 TFLOPS |
| Docked | ~1007 MHz | ~3.1 TFLOPS |

- **Features (✅):** hardware ray tracing, **DLSS** (AI upscaling on the Tensor cores), HDR output, VRR in handheld mode.
- **API:** NVIDIA's proprietary low-level API **NVN2** (successor to NVN on Switch 1) (🔎).

### 1.3 File Decompression Engine (FDE)

A fixed-function hardware block that decompresses game assets without loading the CPU (🔎, NVIDIA driver commits/leaks). Together with fast UFS storage it cuts loading times considerably.

## 2. Main memory (RAM)

| Property | Value | Source |
|---|---|---|
| Capacity | 12 GB | ✅ |
| Type | LPDDR5X | 🔎 |
| Configuration | 2 packages of 6 GB each | 🔎 |
| Supplier | varies by revision: Micron `MT62F768M64D4EK-026` (iFixit unit), SK hynix in other units | 🔎 |
| Bandwidth | ~102 GB/s docked, ~68 GB/s handheld (lower clock) | 🔎 |
| Split | ~9 GB for games, ~3 GB for the OS | 🔎 |

CPU and GPU share the same RAM (**unified memory**); there is no separate video memory.

## 3. Storage

### 3.1 Internal storage

- **256 GB UFS 3.1** (✅). Teardown part: **SK hynix `HN8T15DEHKX075`** (🔎 iFixit).
- UFS is much faster than the Switch 1's eMMC because it supports full-duplex transfers and command queuing.
- **Partitioning (🔎 community analysis):** the UFS device is split into several **LUNs** (logical units). The boot LUNs hold the boot configuration (BCT) and early boot stages (e.g. MB1, PSC firmware), each signed and stored redundantly. The remaining LUNs hold encrypted system, user and game data.

### 3.2 microSD Express

- Only **microSD Express** cards are supported for games (PCIe/NVMe-based, up to ~985 MB/s theoretical) (✅).
- Regular microSD (UHS-I) cards are only recognized for copying screenshots/videos (✅).
- Technically this means the slot is wired to a **PCIe lane** of the SoC, not just a classic SD host controller (🔎).

### 3.3 Game cards

- New, faster card format for Switch 2 games; Switch 1 cards still fit (✅).
- **Game-Key Cards (✅):** cards that contain no game data, only the license key. The game is downloaded, and the card must be inserted to play.
- **Controller:** the board carries a Nintendo custom game card controller, likely **`B2423`** (❓ iFixit: "likely"). On Switch 1 this role was filled by the "Lotus3" chip, which had its own firmware and authenticated each card. A similar design is likely on Switch 2 (❓).

## 4. Cooling & enclosure

- Active cooling with a fan and heat pipe/heatsink over the SoC (🔎).
- The dock also has its own fan, which helps cool the console in TV mode (✅).

## Sources

- [iFixit – Nintendo Switch 2 Chip ID](https://www.ifixit.com/Teardown/Nintendo+Switch+2+Chip+ID/188725)
- [Tom's Hardware – Switch 2 gets disassembled](https://www.tomshardware.com/video-games/nintendo/nintendo-switch-2-gets-disassembled-nvidia-chip-gets-its-close-up)
- [Notebookcheck – Motherboard teardown confirms key specs](https://www.notebookcheck.net/Nintendo-Switch-2-motherboard-teardown-confirms-key-specs.1003950.0.html)
- [TechInsights teardown (Electronics360)](https://electronics360.globalspec.com/article/23293/techinsights-teardown-nintendo-switch-2)
- [Wikipedia – Nintendo Switch 2](https://en.wikipedia.org/wiki/Nintendo_Switch_2)
- [Wccftech – Tegra SoC teardown](https://wccftech.com/nintendo-switch-2-teardown-exposes-the-beautiful-nvidia-tegra-soc/amp/)
