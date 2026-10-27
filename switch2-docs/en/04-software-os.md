# Software: The "Horizon" Operating System

> Note: Nintendo does not publicly document the system. Much of this is known from the Switch 1 (Switchbrew wiki) and, based on analysis so far, largely applies to the Switch 2 as well (🔎). Differences or unknowns are marked ❓.

## 1. Core idea: a microkernel

The Switch 2 runs **Horizon**, an operating system developed in-house by Nintendo. It is **not Linux and not Android**. Horizon originated on the 3DS and was rewritten for the Switch.

- **Microkernel:** the kernel only does the essentials: threads, memory management, interrupts, synchronization and inter-process communication (IPC).
- **Everything else runs in userland:** file system, drivers, networking, input and so on run as separate, isolated **sysmodules**.
- Benefit: if a service crashes or is compromised, the attacker does not automatically get kernel privileges.

## 2. Privilege levels (ARMv8 exception levels)

| Level | What runs there | Source |
|---|---|---|
| EL3 | **Secure Monitor** (TrustZone): key access, power-management calls, sensitive crypto | 🔎 (Switch 1) / ❓ Switch 2 details |
| EL2 | Unused on Switch 1 (no hypervisor). Unclear for Switch 2. | ❓ |
| EL1 | **Horizon kernel** | 🔎 |
| EL0 | Sysmodules, applets, games | 🔎 |

## 3. Key system services (sysmodules)

Services talk to each other over IPC. A process asks the **service manager (`sm`)** for a service, e.g. `fsp-srv`, and gets a **session** over which it sends requests.

| Service | Role |
|---|---|
| `sm` | Service manager: registers services and checks whether a process may use them |
| `pm` | Process manager: starts and terminates processes |
| `ldr` | Loader: loads executables (NSO), checks signatures |
| `fs` | File system: UFS, microSD, game cards, content decryption |
| `ncm` | Content manager: tracks installed content |
| `ns` | Nintendo Shell: application management, launching games |
| `am` | Applet manager: HOME menu, focus, suspend |
| `hid` | Input: Joy-Con, touch, mouse sensor |
| `nvservices` | NVIDIA GPU driver (userland) |
| `audio` | Audio output |
| `bsdsockets`, `nifm`, `ssl` | Networking, connection management, TLS |
| `account` | User accounts / Nintendo Account |
| `es` | **eTicket service**: licenses (tickets) for digital games |
| `nim` | eShop downloads/installs, system updates |
| `spl` / `csrng` | Access to the Secure Monitor's crypto and RNG functions |

(List based on the Switch 1 architecture, 🔎. The Switch 2 adds services, e.g. for GameChat, the camera, mouse input and Game-Key Cards ❓.)

## 4. Applets and games

- **System applets:** HOME menu (`qlaunch`), overlay (quick menu), settings, eShop, album, user selector, etc.
- **Applications:** each game runs as its own sandboxed process. It may only use the services allowed in its metadata (NPDM), which Nintendo signs.
- **Graphics:** games use **NVN2** directly (very close to the hardware) and can use DLSS and ray tracing.

## 5. File formats & content (🔎, carried over from Switch 1)

| Format | Meaning |
|---|---|
| **NCA** | Nintendo Content Archive: encrypted, signed container for code, data and metadata |
| **NSO** | Executable format (compressed ELF derivative) |
| **NPDM** | Program metadata: permissions, allowed services, syscalls |
| **Ticket** | License for digital content (bound to account/console) |

## 6. Updates & version numbers

- Switch 1 and Switch 2 share one version number series. The Switch 2 launched on **system version 20.x** (🔎). As of autumn 2026 the current line is 23.x (🔎).
- Updates are signed and delivered over the internet or on game cards.
- Some updates burn **fuses** so that an older version can no longer boot (anti-downgrade, see [05-security.md](05-security.md)).

## 7. Backward compatibility with Switch 1

- Most Switch 1 games run on Switch 2 (✅). Nintendo maintains a list of exceptions.
- **CPU code:** A57 and A78C are both ARMv8, so the code runs natively.
- **GPU code:** Switch 1 games ship pre-compiled **Maxwell shaders**, which Ampere cannot run directly. The Switch 2 therefore uses a **translation layer** that converts shaders and GPU commands for Ampere (🔎). This explains some graphical glitches and incompatible titles.
- **"Nintendo Switch 2 Edition"** releases and free updates give some Switch 1 games native improvements (✅).

## 8. New software features

| Feature | Description | Source |
|---|---|---|
| **GameChat** | Voice and video chat plus screen sharing, triggered by the C button | ✅ |
| **Virtual Game Cards** | Digital games can be "moved" between two consoles and lent within a family group | ✅ |
| **Game-Key Cards** | Physical card used as a license; the game is downloaded | ✅ |
| **Mouse controls** | New `hid` input type via the Joy-Con 2 sensor | ✅ / 🔎 (service) |
| **Parental controls** | Extended controls incl. GameChat approval via the app | ✅ |

## Sources

- [Switchbrew (Switch 1 documentation, basis for much of this)](https://switchbrew.org/wiki/Main_Page)
- [Switchbrew – Boot2](https://switchbrew.org/wiki/Boot2)
- [Wikipedia – Nintendo Switch 2](https://en.wikipedia.org/wiki/Nintendo_Switch_2)
- [SwitchTools – Switch 2 software summary (X)](https://x.com/SwitchTools/status/1937118212933439514)
