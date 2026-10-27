# Hardware Teil 1: SoC, CPU, GPU, RAM, Speicher

## 1. Das SoC: NVIDIA T239

Das Herzstück ist ein Custom-Chip von NVIDIA. Er heißt intern **T239** und trägt auf dem Package den Aufdruck **`GMLX30-A1`** (🔎 iFixit, Tom's Hardware). Er vereint CPU, GPU, Speichercontroller, Video-Engines, Display-Controller, USB-Controller (xHCI) und Sicherheits-Hardware auf einem Die.

| Eigenschaft | Wert | Quelle |
|---|---|---|
| Fertigung | Samsung 8 nm (8N) | 🔎 |
| Architektur-Basis | Ableger der Tegra-Orin-Familie | 🔎 |
| CPU | 8× Cortex-A78C | 🔎 |
| GPU | Ampere (GA10x-Generation) | 🔎 |
| Speicherinterface | 128 bit LPDDR5X | 🔎 |
| Sonderblöcke | File Decompression Engine (FDE), NVENC/NVDEC, Display-Controller | 🔎 |

### 1.1 CPU

- **8 Kerne ARM Cortex-A78C** (ARMv8.2-A, 64 bit). Die „C“-Variante ist für Notebooks/Embedded gedacht und erlaubt bis zu 8 große Kerne in einem Cluster mit gemeinsamem L3-Cache.
- **Aufteilung (🔎, Entwickler-Leaks):** 6 Kerne für Spiele, 2 Kerne für das Betriebssystem und Hintergrunddienste.
- **Takt (🔎, Digital Foundry / Leak-Dokumente):** ca. 998 MHz für Spiele im Handheld- und TV-Modus, optional bis ca. 1,1 GHz. Für das System sind höhere Takte (bis ~1,7 GHz) belegt, z. B. beim Laden.
- Kein Big.LITTLE: Alle Kerne sind gleich, was die Planung für Spieleentwickler vereinfacht.

### 1.2 GPU

- **Architektur:** NVIDIA Ampere (gleiche Generation wie die RTX 30-Serie).
- **Ausstattung (🔎):** 12 Streaming Multiprocessors (SMs) = **1536 CUDA-Kerne**, 48 Tensor-Kerne, 12 RT-Kerne.
- **Takt und Leistung (🔎):**

| Modus | GPU-Takt | FP32-Leistung (ca.) |
|---|---|---|
| Handheld | ~561 MHz | ~1,7 TFLOPS |
| TV (Dock) | ~1007 MHz | ~3,1 TFLOPS |

- **Funktionen (✅):** Hardware-Raytracing, **DLSS** (KI-Upscaling über die Tensor-Kerne), HDR-Ausgabe, VRR im Handheld.
- **API:** NVIDIAs proprietäres Low-Level-API **NVN2** (Nachfolger von NVN aus der Switch 1) (🔎).

### 1.3 File Decompression Engine (FDE)

Ein fester Hardware-Block, der komprimierte Spieldaten (Assets) entpackt, ohne die CPU zu belasten (🔎, NVIDIA-Treiber-Commits/Leaks). Zusammen mit dem schnellen UFS-Speicher verkürzt er die Ladezeiten deutlich.

## 2. Arbeitsspeicher (RAM)

| Eigenschaft | Wert | Quelle |
|---|---|---|
| Kapazität | 12 GB | ✅ |
| Typ | LPDDR5X | 🔎 |
| Bestückung | 2 Chips à 6 GB | 🔎 |
| Hersteller | je nach Revision unterschiedlich: Micron `MT62F768M64D4EK-026` (iFixit-Gerät) und SK hynix in anderen Geräten | 🔎 |
| Bandbreite | ~102 GB/s im Dock, ~68 GB/s im Handheld (niedrigerer Takt) | 🔎 |
| Aufteilung | ~9 GB für Spiele, ~3 GB fürs Betriebssystem | 🔎 |

CPU und GPU teilen sich den RAM (**Unified Memory**), es gibt also keinen separaten Grafikspeicher.

## 3. Massenspeicher

### 3.1 Interner Speicher

- **256 GB UFS 3.1** (✅). Teardown-Teil: **SK hynix `HN8T15DEHKX075`** (🔎 iFixit).
- UFS ist deutlich schneller als das eMMC der Switch 1, weil es Vollduplex-Übertragung und Command Queuing beherrscht.
- **Partitionierung (🔎 Community-Analyse):** Der UFS-Speicher ist in mehrere **LUNs** (Logical Units) aufgeteilt. Die Boot-LUNs enthalten die Boot-Konfiguration (BCT) und die frühen Boot-Stufen (z. B. MB1, PSC-Firmware), jeweils signiert und redundant gespeichert. Die übrigen LUNs enthalten System-, Benutzer- und Spieledaten, die verschlüsselt sind.

### 3.2 microSD Express

- Unterstützt werden nur **microSD-Express-Karten** (PCIe/NVMe-basiert, bis ~985 MB/s theoretisch) (✅).
- Normale microSD-Karten (UHS-I) werden nur zum Kopieren von Screenshots/Videos erkannt, nicht für Spiele (✅).
- Technisch bedeutet das: Der Slot hängt an einer **PCIe-Lane** des SoC, nicht nur am klassischen SD-Host-Controller (🔎).

### 3.3 Game Cards (Spielmodule)

- Neues, schnelleres Kartenformat für Switch-2-Spiele; Switch-1-Karten passen weiterhin (✅).
- **Game-Key-Cards (✅):** Karten, auf denen kein Spiel liegt, sondern nur der Lizenzschlüssel. Das Spiel wird heruntergeladen, die Karte muss zum Starten eingesteckt sein.
- **Controller:** Auf dem Board sitzt ein Nintendo-eigener Game-Card-Controller, vermutlich **`B2423`** (❓ iFixit: „likely“). Bei der Switch 1 übernahm diese Aufgabe der „Lotus3“-Chip mit eigener Firmware und Authentifizierung der Karte. Für Switch 2 ist eine ähnliche Architektur wahrscheinlich (❓).

## 4. Kühlung & Gehäuse

- Aktive Kühlung mit Lüfter und Heatpipe/Kühlkörper über dem SoC (🔎).
- Auch das Dock hat einen eigenen Lüfter, der die Konsole im TV-Modus mitkühlt (✅).

## Quellen

- [iFixit – Nintendo Switch 2 Chip ID](https://www.ifixit.com/Teardown/Nintendo+Switch+2+Chip+ID/188725)
- [Tom's Hardware – Switch 2 gets disassembled](https://www.tomshardware.com/video-games/nintendo/nintendo-switch-2-gets-disassembled-nvidia-chip-gets-its-close-up)
- [Notebookcheck – Motherboard teardown confirms key specs](https://www.notebookcheck.net/Nintendo-Switch-2-motherboard-teardown-confirms-key-specs.1003950.0.html)
- [TechInsights-Teardown (Electronics360)](https://electronics360.globalspec.com/article/23293/techinsights-teardown-nintendo-switch-2)
- [Wikipedia – Nintendo Switch 2](https://en.wikipedia.org/wiki/Nintendo_Switch_2)
- [Wccftech – Teardown des Tegra-SoC](https://wccftech.com/nintendo-switch-2-teardown-exposes-the-beautiful-nvidia-tegra-soc/amp/)
