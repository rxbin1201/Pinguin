# Known Issues: Hardware & Security Vulnerabilities

As of: **2026-10-27**

> Nintendo publishes no failure statistics, and no recall is known. Most information comes from teardowns, reviews, repair shops and forums, so how common an issue is usually cannot be determined.

## Part A: Hardware

### A.1 Joy-Con 2 drift

| | |
|---|---|
| **Symptom** | The stick reports movement without being touched ("phantom inputs") |
| **Cause** | According to iFixit's teardown, the Joy-Con 2 uses nearly the same stick modules as the 2017 Joy-Con: **potentiometers** with a graphite wiper on a resistive track. Friction and wear shift the reading. |
| **Why no Hall-effect sensors?** | Hall-effect sticks measure contactlessly via magnetic fields and barely wear. The Joy-Con 2's **magnetic attachment** would probably interfere with them (🔎). |
| **Prevalence** | First reports shortly after launch (June 2025); repair shops still report cases in 2026 |
| **Remedy** | Stick calibration in system settings (limited help), repair/replacement through Nintendo |
| **Reliability** | 🔎 high (teardown + many reports) |

### A.2 Display

| Issue | Details | Reliability |
|---|---|---|
| **Ghosting / smearing** | The LCD has slow pixel response times, so moving objects leave visible trails, especially on dark backgrounds. Digital Foundry criticizes this in its review. | 🔎 high |
| **Weak HDR** | The LCD supports HDR10 but barely reaches HDR-worthy brightness and contrast (no local dimming) | 🔎 high |
| **Panel revision** | Rumors of an improved LCD in later units, which would mean different displays depending on the batch ("hardware lottery") | ❓ rumor |
| **Scratches** | The factory screen layer is **soft plastic**, not glass, and scratches easily. Nintendo itself warns about scratches when using mouse controls on rough surfaces. A screen protector is recommended. | 🔎 high |

### A.3 Battery

- Isolated reports of **swollen batteries**, where the rear panel visibly separates from the chassis.
- This is a **safety risk** (fire hazard): stop charging and have the device repaired.
- Prevalence unclear, no official statement (❓).

### A.4 Mechanics & ports

| Part | Report | Reliability |
|---|---|---|
| Kickstand | Hinges loosen over time | ❓ anecdotal |
| USB-C port | Some report loose connections; a repair technician, by contrast, praised the **reinforced** port | ❓ conflicting |
| Speaker grille | Grille gets dirty or deformed | ❓ anecdotal |
| Game card slot | **Counterfeit cartridges** with 3D-printed shells can permanently damage the reader mechanically. This is damage from third-party parts, not a manufacturing defect. | ❓ single source |

### A.5 Compatibility

- Many **third-party docks** and some USB-C chargers do not work or only partly work, likely because of a proprietary handshake with the dock's microcontroller (see [03-hardware-io-peripherals.md](03-hardware-io-peripherals.md)) (🔎).
- Regular **microSD cards** (non-Express) are not accepted for games. This is by design, not a defect (✅).

### A.6 Repairability

Teardowns rate the Switch 2 as **hard to repair**: glued components, difficult opening, tedious battery replacement (🔎).

---

## Part B: Security vulnerabilities

### B.1 Overview

So far **only userland vulnerabilities** are known, i.e. flaws in the layer where games and apps run inside their sandbox. There is no publicly confirmed **kernel exploit** or **BootROM exploit**. Nintendo can close userland flaws with system updates.

```
Attack layer                     Status Oct 2026
─────────────────────────────────────────────────
BootROM / boot chain (PSC, MB1)  ✗ nothing known
Secure Monitor (EL3)             ✗ nothing known
Kernel (EL1)                     ✗ nothing confirmed (speculation only)
System services (EL0)            ◐ ns2jb: code with some services' permissions
Games / apps (EL0, sandbox)      ✓ several userland exploits
```

### B.2 Timeline

| Date | Name / ID | Type | Impact | Reliability |
|---|---|---|---|---|
| June 2025 | first userland demo | ROP (return-oriented programming) via a game | code execution only inside the game process; practically no impact | 🔎 |
| July 2026 | **Gezine exploit** | universal userland exploit, offline, on all firmware versions, without WebKit or save transfers | stays inside the app sandbox, no custom firmware, no piracy. Unclear whether it has been released. | 🔎 Notebookcheck, Wccftech |
| Sep 2026 | **CVE-2026-82079** | stack buffer overflow in local wireless communication (QR code feature), CVSS ~8.4 | **affects Switch 1 only**; Nintendo says it cannot be exploited on Switch 2. Fixed in 23.0.0. | 🔎 SC World, CyberInsider |
| Oct 2026 | **ns2jb** (pepsipu) | integer overflow in the *SmileBASIC* interpreter, firmware 23.0.1 | native code with certain system services' permissions, **tethered** (re-run after every reboot), no kernel access, no persistent CFW. Nintendo reportedly blocks access to the required software. | 🔎 Kotaku, Ars Technica, VideoCardz |
| Oct 2026 | firmware dump / PC emulator | claims | **unverified**, conflicting reports | ❓ |
| 2026 | **CVE-2025-10263** (ARM erratum 4193794) | possible kernel privilege escalation via a CPU erratum | pure **forum speculation**, not confirmed by Nintendo | ❓ GBAtemp |

### B.3 How Nintendo responds

1. **System updates** close userland flaws. Fuse-based anti-downgrade prevents going back to vulnerable versions (see [05-security.md](05-security.md)).
2. **Cutting off the entry point:** e.g. making the affected game or its content unavailable (reported for ns2jb).
3. **Online bans:** consoles showing suspicious patterns (e.g. cloned game card IDs from MIG flash carts, June 2025) are banned from online services.
4. **Terms of use:** allow Nintendo to render tampered consoles wholly or partly unusable.

### B.4 Assessment

- The Switch 1 was mainly vulnerable through an **unpatchable BootROM bug**. Nothing comparable is known for the Switch 2.
- The risk for regular users is low: all known flaws require local access or deliberate action, and the only critical CVE affects the Switch 1.
- **Recommendation:** install system updates and use only official game cards and accessories.

## Sources

**Hardware**
- [Design News – Repairability Issues & Design Flaws](https://www.designnews.com/electronics/nintendo-switch-2-teardown-reveals-poor-repairability-persistent-design-flaws)
- [4Gamers – Most Common Switch 2 Issues](https://www.4gamers.net/post/more-than-a-year-later-these-are-the-most-common-nintendo-switch-2-issues)
- [Harktech – Joy-Con Drift 2026 Field Report](https://harktech.co.uk/help/nintendo-switch-2-joycon-drift-2026-field-report)
- [MobileSyrup – iFixit: Joy-Cons can still drift](https://mobilesyrup.com/2025/06/06/ifixit-report-says-switch-2-joy-cons-can-still-drift/)
- [ShopSavvy – Joy-Con drift](https://shopsavvy.com/answers/does-the-nintendo-switch-2-have-joy-con-drift-problems)
- [LevelUp – Early Joy-Con Drift Doubts](https://www.levelup.com/en/news/switch-2-faces-early-joy-con-drift-doubts)
- [Notebookcheck – Joy-Con issues, not drift](https://www.notebookcheck.net/Switch-2-users-reporting-Joy-Con-issues-but-it-s-not-stick-drift.1039361.0.html)
- [MacMyths – Early problems](https://macmyths.com/nintendo-switch-2-early-problems-bugs-and-hardware-issues/)
- [Famiboards – Digital Foundry Hardware Review](https://famiboards.com/threads/digital-foundry-nintendo-switch-2-df-hardware-review-a-satisfying-upgrade-but-display-issues-are-problematic.14191/)
- [Wccftech – LCD revision](https://wccftech.com/nintendo-switch-2-hardware-lottery-lcd-revision/)
- [Technetbooks – Port failure by counterfeit carts](https://www.technetbooks.com/2026/05/nintendo-switch-2-hardware-failure.html)

**Security**
- [SC World – Nintendo patches critical vulnerability](https://www.scworld.com/brief/nintendo-patches-critical-nintendo-switch-vulnerability)
- [CyberInsider – QR code flaw](https://cyberinsider.com/nintendo-warns-of-switch-code-execution-flaw-via-on-screen-qr-codes/)
- [Tom's Guide – Severe vulnerability patched](https://www.tomsguide.com/news/nintendo-switch-severe-vulnerability-patched-what-you-need-to-know)
- [Notebookcheck – Universal offline exploit](https://www.notebookcheck.net/Switch-2-Developer-unveils-a-universal-exploit-that-works-entirely-offline.1347373.0.html)
- [Wccftech – Gezine universal exploit](https://wccftech.com/nintendo-switch-2-security-developer-gezine-cracks-universal-exploit-offline/)
- [VideoCardz – Nintendo blocks exploit software](https://videocardz.com/newz/nintendo-reportedly-blocks-access-to-switch-2-exploit-software-first-homebrew-tests-demonstrated)
- [Kotaku – First jailbreak](https://kotaku.com/nintendo-switch-2-jailbreak-hack-exploit-piracy-homebrew-emulation-modding-2000748784)
- [GBAtemp – CVE-2025-10263 (speculation)](https://gbatemp.net/threads/research-cve-2025-10263-arm-erratum-4193794-potential-kernel-escalation-on-switch-2.684099/)
