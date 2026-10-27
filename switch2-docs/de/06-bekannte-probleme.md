# Bekannte Probleme: Hardware & Sicherheitslücken

Stand: **2026-10-27**

> Nintendo veröffentlicht keine Ausfallstatistiken. Ein Rückruf ist nicht bekannt. Die meisten Angaben stammen aus Teardowns, Tests, Reparaturbetrieben und Foren. Wie häufig ein Problem ist, lässt sich daher meist nicht sagen.

## Teil A: Hardware

### A.1 Joy-Con-2-Drift

| | |
|---|---|
| **Symptom** | Der Stick meldet Bewegung, obwohl er nicht berührt wird („Phantom-Eingaben“) |
| **Ursache** | Laut iFixit-Teardown nutzen die Joy-Con 2 fast dieselben Stick-Module wie die Joy-Con von 2017: **Potentiometer** mit Graphit-Schleifer auf einer Widerstandsbahn. Durch Reibung und Abrieb verändert sich der Messwert. |
| **Warum keine Hall-Sensoren?** | Hall-Effekt-Sticks messen berührungslos über Magnetfelder und verschleißen kaum. Die **magnetische Befestigung** der Joy-Con 2 würde sie jedoch vermutlich stören (🔎). |
| **Verbreitung** | Erste Berichte kurz nach dem Start (Juni 2025), Reparaturbetriebe melden 2026 weiterhin Fälle |
| **Abhilfe** | Stick-Kalibrierung in den Systemeinstellungen (hilft nur begrenzt), Reparatur bzw. Austausch über Nintendo |
| **Verlässlichkeit** | 🔎 hoch (Teardown + viele Berichte) |

### A.2 Display

| Problem | Details | Verlässlichkeit |
|---|---|---|
| **Ghosting / Schlieren** | Das LCD hat langsame Pixel-Schaltzeiten. Bewegte Objekte ziehen sichtbare Schlieren, vor allem auf dunklem Hintergrund. Digital Foundry kritisiert das in ihrem Test. | 🔎 hoch |
| **Schwaches HDR** | Das LCD ist zwar HDR10-fähig, erreicht aber kaum HDR-taugliche Helligkeit und Kontraste (kein Local Dimming) | 🔎 hoch |
| **Panel-Revision** | Gerüchte über ein verbessertes LCD in späteren Geräten. Dann hätten die Konsolen je nach Charge unterschiedliche Displays („Hardware-Lotterie“). | ❓ Gerücht |
| **Kratzer** | Die Schutzschicht ab Werk ist **weicher Kunststoff**, kein Glas, und verkratzt schnell. Nintendo warnt selbst vor Kratzern, wenn die Maussteuerung auf rauen Oberflächen genutzt wird. Eine Schutzfolie wird empfohlen. | 🔎 hoch |

### A.3 Akku

- Einzelberichte über **aufgeblähte Akkus**: Die Rückseite löst sich sichtbar vom Gehäuse.
- Das ist ein **Sicherheitsrisiko** (Brandgefahr): Gerät nicht mehr laden, sondern reparieren lassen.
- Verbreitung unklar, keine offizielle Stellungnahme (❓).

### A.4 Mechanik & Anschlüsse

| Teil | Bericht | Verlässlichkeit |
|---|---|---|
| Ständer | Scharniere lockern sich mit der Zeit | ❓ anekdotisch |
| USB-C-Buchse | Einige berichten über wackelige Steckverbindungen. Ein Reparaturtechniker lobt dagegen die **verstärkte** Buchse. | ❓ widersprüchlich |
| Lautsprechergitter | Verschmutzung/Verformung des Gitters | ❓ anekdotisch |
| Game-Card-Slot | **Gefälschte Spielmodule** mit 3D-gedrucktem Gehäuse können den Leser mechanisch dauerhaft beschädigen. Das ist ein Schaden durch Fremdteile, kein Herstellerfehler. | ❓ einzelne Quelle |

### A.5 Kompatibilität

- Viele **Fremd-Docks** und manche USB-C-Netzteile funktionieren nicht oder nur eingeschränkt, vermutlich wegen eines proprietären Handshakes mit dem Dock-Mikrocontroller (siehe [03-hardware-io-peripherie.md](03-hardware-io-peripherie.md)) (🔎).
- Normale **microSD-Karten** (ohne „Express“) werden für Spiele nicht akzeptiert. Das ist Absicht, kein Defekt (✅).

### A.6 Reparierbarkeit

Teardowns bewerten die Switch 2 als **schwer reparierbar**: verklebte Komponenten, schwieriges Öffnen, Akkutausch aufwendig (🔎).

---

## Teil B: Sicherheitslücken

### B.1 Übersicht

Bisher sind **nur Userland-Lücken** bekannt, also Lücken in der Ebene, in der Spiele und Apps in ihrer Sandbox laufen. Einen öffentlich bestätigten **Kernel-Exploit** oder **BootROM-Exploit** gibt es nicht. Nintendo kann Userland-Lücken per Systemupdate schließen.

```
Angriffsebene                    Stand Okt. 2026
─────────────────────────────────────────────────
BootROM / Boot-Kette (PSC, MB1)  ✗ nichts bekannt
Secure Monitor (EL3)             ✗ nichts bekannt
Kernel (EL1)                     ✗ nichts bestätigt (nur Spekulation)
Systemdienste (EL0)              ◐ ns2jb: Code mit Rechten bestimmter Dienste
Spiele / Apps (EL0, Sandbox)     ✓ mehrere Userland-Exploits
```

### B.2 Chronologie

| Datum | Name / Kennung | Art | Auswirkung | Verlässlichkeit |
|---|---|---|---|---|
| Juni 2025 | erste Userland-Demo | ROP (Return-Oriented Programming) über ein Spiel | Code-Ausführung nur im Spielprozess, praktisch ohne Folgen | 🔎 |
| Juli 2026 | **Gezine-Exploit** | universeller Userland-Exploit, offline, auf allen Firmware-Versionen, ohne WebKit oder Spielstand-Transfer | bleibt in der App-Sandbox, keine Custom Firmware, keine Raubkopien. Ob er veröffentlicht wurde, ist unklar. | 🔎 Notebookcheck, Wccftech |
| Sep. 2026 | **CVE-2026-82079** | Stack-Buffer-Overflow in der lokalen Drahtlos-Kommunikation (QR-Code-Funktion), CVSS ~8,4 | **nur Switch 1 betroffen**; laut Nintendo auf der Switch 2 nicht ausnutzbar. Behoben in 23.0.0. | 🔎 SC World, CyberInsider |
| Okt. 2026 | **ns2jb** (pepsipu) | Integer-Overflow im Interpreter von *SmileBASIC*, Firmware 23.0.1 | nativer Code mit den Rechten bestimmter Systemdienste, **tethered** (nach jedem Neustart neu), kein Kernel, keine dauerhafte CFW. Nintendo blockiert laut Berichten den Zugang zur benötigten Software. | 🔎 Kotaku, Ars Technica, VideoCardz |
| Okt. 2026 | Firmware-Dump / PC-Emulator | Behauptungen | **nicht verifiziert**, widersprüchliche Berichte | ❓ |
| 2026 | **CVE-2025-10263** (ARM-Erratum 4193794) | mögliche Kernel-Rechteausweitung über einen CPU-Fehler | reine **Forumsspekulation**, keine Bestätigung von Nintendo | ❓ GBAtemp |

### B.3 Wie Nintendo reagiert

1. **Systemupdates** schließen Userland-Lücken. Das Anti-Downgrade per Fuses verhindert ein Zurückgehen auf verwundbare Versionen (siehe [05-sicherheit.md](05-sicherheit.md)).
2. **Zugang zur Einstiegssoftware sperren:** z. B. wenn das betroffene Spiel bzw. seine Inhalte nicht mehr verfügbar sind (bei ns2jb berichtet).
3. **Online-Sperren:** Konsolen mit auffälligen Mustern (z. B. kopierte Game-Card-IDs von MIG-Flashkarten, Juni 2025) werden für Online-Dienste gesperrt.
4. **Nutzungsbedingungen:** erlauben Nintendo, manipulierte Konsolen ganz oder teilweise unbrauchbar zu machen.

### B.4 Einordnung

- Die Switch 1 war vor allem durch einen **unpatchbaren BootROM-Fehler** angreifbar. Bei der Switch 2 ist so etwas bisher nicht bekannt.
- Für normale Nutzer ist das Risiko gering: Alle bekannten Lücken brauchen einen lokalen Zugriff bzw. aktives Zutun, und die einzige kritische CVE betrifft die Switch 1.
- **Empfehlung:** Systemupdates installieren und nur offizielle Spielmodule und Zubehör nutzen.

## Quellen

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
- [Wccftech – LCD-Revision](https://wccftech.com/nintendo-switch-2-hardware-lottery-lcd-revision/)
- [Technetbooks – Port failure by counterfeit carts](https://www.technetbooks.com/2026/05/nintendo-switch-2-hardware-failure.html)

**Sicherheit**
- [SC World – Nintendo patches critical vulnerability](https://www.scworld.com/brief/nintendo-patches-critical-nintendo-switch-vulnerability)
- [CyberInsider – QR code flaw](https://cyberinsider.com/nintendo-warns-of-switch-code-execution-flaw-via-on-screen-qr-codes/)
- [Tom's Guide – Severe vulnerability patched](https://www.tomsguide.com/news/nintendo-switch-severe-vulnerability-patched-what-you-need-to-know)
- [Notebookcheck – Universal offline exploit](https://www.notebookcheck.net/Switch-2-Developer-unveils-a-universal-exploit-that-works-entirely-offline.1347373.0.html)
- [Wccftech – Gezine universal exploit](https://wccftech.com/nintendo-switch-2-security-developer-gezine-cracks-universal-exploit-offline/)
- [VideoCardz – Nintendo blocks exploit software](https://videocardz.com/newz/nintendo-reportedly-blocks-access-to-switch-2-exploit-software-first-homebrew-tests-demonstrated)
- [Kotaku – First jailbreak](https://kotaku.com/nintendo-switch-2-jailbreak-hack-exploit-piracy-homebrew-emulation-modding-2000748784)
- [GBAtemp – CVE-2025-10263 (Spekulation)](https://gbatemp.net/threads/research-cve-2025-10263-arm-erratum-4193794-potential-kernel-escalation-on-switch-2.684099/)
