# Switch 2 Security Mechanisms

> For information only: this explains the architecture and is not a guide to bypassing it. Many details come only from Switch 1 research or from the community (🔎/❓).

## 1. Nintendo's goals

1. Only **signed Nintendo code** may run (no homebrew, no piracy).
2. **Keys** must never leave the hardware in plaintext.
3. **Downgrades** to older, vulnerable firmware should be prevented.
4. Tampered consoles should be **detected and banned online**.

## 2. Lessons from the Switch 1

The Switch 1 (Erista, Tegra X1) had a **BootROM bug** (Fusée Gelée, CVE-2018-6242). Through the USB recovery mode (RCM), custom code could run before any signature check. Because the BootROM is baked into the chip, this was **not fixable by an update**. Later models (Mariko) could only be broken with a **modchip using voltage glitching**.

According to community analysis, NVIDIA and Nintendo hardened the T239 against exactly these two attack paths: the RCM-style USB recovery path and fault injection/glitching (🔎/❓).

## 3. Secure boot chain

Each stage verifies the signature of the next before running it (**chain of trust**):

```
1. BootROM (mask ROM in the chip, immutable)
   │  reads the BCT (Boot Configuration Table) from the UFS boot LUN
   │  verifies its signature against a key hash stored in fuses
   ▼
2. PSC firmware  ─ Platform Security Controller (dedicated security processor)
   MB1 / MBCT    ─ early boot stages (memory init, configuration)
   │  (signed, stored redundantly)                               🔎
   ▼
3. Package1 / Secure Monitor (EL3, TrustZone)                    🔎/❓
   ▼
4. Package2: Horizon kernel + core sysmodules                    🔎
   ▼
5. Remaining system services, HOME menu, games
```

- **PSC (Platform Security Controller):** newer NVIDIA Tegra chips include a separate security processor that manages keys and verifies boot stages. It roughly replaces the Switch 1's TSEC (Falcon) (🔎/❓).
- According to community analysis, the power-management processor is treated as **untrusted** on Switch 2. On Switch 1 it was an attack vector (❓).

## 4. eFuses (one-time programmable fuses)

Fuses are tiny cells in the SoC that can be burned from 0 to 1 **once only**.

- They store, among other things, the **hash of the public boot key**, the **production mode** flag and device-specific values.
- **Redundancy (🔎 Switchbrew):** the first 80 fuse words are stored as 40 redundant pairs, and both values must match. This makes it harder to cause a misread through targeted faults (glitching).
- **Anti-downgrade:** on Switch 1, important updates burned fuses so that booting older firmware fails. The same principle is very likely on Switch 2 (❓).

## 5. Keys & cryptography

- Device-specific keys are derived inside the security hardware and **never sit in RAM in plaintext** (🔎 Switch 1 principle).
- Games and apps can only request crypto operations indirectly through the Secure Monitor (`spl` service).
- **Storage encryption:** the system and user partitions on UFS are encrypted (on Switch 1: AES-XTS with device-specific "BIS keys") (🔎).
- **Content (NCA):** encrypted **and** signed. Tampered files are rejected at load time.
- **microSD:** content on the SD card is encrypted and bound to the console (🔎).

## 6. Runtime protection in the OS

| Mechanism | Effect |
|---|---|
| **Microkernel + sandbox** | Every service and every game is an isolated process with its own address space |
| **Permission declaration (NPDM/ACID)** | A program may only use the syscalls and services listed in its signed metadata |
| **Code signing at load time** | The loader verifies executables; there is no path to load unsigned code |
| **W^X / NX** | Memory is either writable or executable, never both (no JIT for games) |
| **ASLR** | Randomized memory addresses make exploits harder |
| **Modern ARM mitigations** | ARMv8.2 (A78C) enables e.g. PAN/UAO. Whether Nintendo uses pointer authentication or similar is not publicly known (❓) |

## 7. Licenses & game cards

- **eTickets (`es` service):** digital purchases are bound to the Nintendo Account and console via a **ticket**.
- **Virtual Game Cards:** the license is assigned to a console on the server side; "moving" a card transfers it online between consoles (✅ feature, mechanism 🔎).
- **Game cards:** the game card controller authenticates the card cryptographically before reading content (on Switch 1 via the Lotus3 chip, 🔎; a comparable scheme is assumed on Switch 2, ❓).
- Each game card has a **unique identifier/certificate**, which lets Nintendo spot copied cards online.

## 8. Online protection & bans

- The console authenticates to Nintendo's servers with a **device certificate** (🔎).
- Nintendo detects suspicious patterns on the server side, e.g. the same game card ID showing up on many consoles.
- **Real-world example (✅ reported in the press, June 2025):** users of "MIG Switch" flash carts (copies of Switch 1 games) were **banned online** on Switch 2 shortly after launch.
- **Terms of use (✅):** in 2025 Nintendo changed its terms so that, for unauthorized modification or piracy, it may render the console "permanently unusable in whole or in part".

## 9. State of security research (October 2026)

| Date | Event | Reliability |
|---|---|---|
| June 2025 | First **userland exploits** (ROP in a game) demonstrated publicly, with no kernel or boot access | 🔎 |
| July 2026 | **Gezine exploit**: universal userland exploit, offline, on all firmware versions, stays inside the sandbox | 🔎 |
| Oct 2026 | **"ns2jb"** (researcher: pepsipu) for system version **23.0.1**: software-only, **tethered** jailbreak that must be re-run after every reboot | 🔎 Kotaku; scope disputed |
| Oct 2026 | Claims of a full firmware dump and a working PC emulator | ❓ **unverified** |
| – | **No** known BootROM exploit, no persistent custom firmware, no confirmed modchip | per current reports |

Bottom line: the Switch 2 is much better protected than the Switch 1. The BootROM → PSC → signed-stage chain is so far considered unbroken. Known attacks target userland or system software and can be patched by updates.

## Sources

- [Switchbrew – Switch 2: Fuses](https://switchbrew.org/wiki/Switch_2:_Fuses)
- [Switchbrew – Fuses (Switch 1)](https://switchbrew.org/wiki/Fuses)
- [Switchbrew – Switch System Flaws](https://switchbrew.org/wiki/Switch_System_Flaws)
- [SwitchTools – UFS LUNs and boot stages (X)](https://x.com/SwitchTools/status/1937118212933439514)
- [GBAtemp – Switch 2 hardening against RCM/glitching (forum)](https://gbatemp.net/threads/let-me-save-you-the-suspense-the-switch-2-wont-get-hacked.676435/)
- [GBAtemp – Modchip attack vectors (forum)](https://gbatemp.net/threads/switch-2-data-gathering-for-possible-modchip-attack-vectors.668520/)
- [Kotaku – The Switch 2 Has Been Jailbroken For The First Time](https://kotaku.com/nintendo-switch-2-jailbreak-hack-exploit-piracy-homebrew-emulation-modding-2000748784)
- [Techyorker – What ns2jb actually proves](https://techyorker.com/switch-2-firmware-dump-23-0-1-what-the-ns2jb-exploit-actually-proves-and-why-theres-no-emulator/)
- [Wayayeo – Modding status August 2026](https://wayayeo.org/nintendo-switch-2-modding-early-homebrew-and-hack-news/)
