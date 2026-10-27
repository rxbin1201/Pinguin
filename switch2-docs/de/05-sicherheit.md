# Sicherheitsmechanismen der Switch 2

> Rein informativ: Das Dokument erklärt die Architektur, keine Anleitung zum Umgehen. Viele Details sind nur aus der Analyse der Switch 1 oder aus der Community bekannt (🔎/❓).

## 1. Ziele von Nintendo

1. Nur **signierter Code** von Nintendo darf laufen (kein Homebrew, keine Raubkopien).
2. **Schlüssel** dürfen die Hardware nie im Klartext verlassen.
3. **Downgrades** auf ältere, verwundbare Firmware sollen verhindert werden.
4. Manipulierte Konsolen sollen **online erkannt und gesperrt** werden.

## 2. Lehren aus der Switch 1

Die Switch 1 (Erista, Tegra X1) hatte einen **Fehler im BootROM** (Fusée Gelée, CVE-2018-6242). Über den USB-Wiederherstellungsmodus (RCM) ließ sich vor jeder Signaturprüfung eigener Code ausführen. Weil das BootROM fest im Chip ist, war das **nicht per Update behebbar**. Spätere Modelle (Mariko) wurden nur noch per **Modchip mit Voltage-Glitching** geknackt.

Für den T239 haben NVIDIA und Nintendo laut Community-Analysen genau diese beiden Angriffswege gezielt gehärtet: den RCM-artigen USB-Recovery-Pfad und Fault-Injection/Glitching (🔎/❓).

## 3. Secure-Boot-Kette

Jede Stufe prüft die Signatur der nächsten, bevor sie diese ausführt (**Chain of Trust**):

```
1. BootROM (im Chip maskiert, unveränderlich)
   │  liest BCT (Boot Configuration Table) aus der Boot-LUN des UFS
   │  prüft Signatur mit Schlüssel-Hash in den Fuses
   ▼
2. PSC-Firmware  ─ Platform Security Controller (eigener Sicherheitsprozessor)
   MB1 / MBCT    ─ frühe Boot-Stufen (Speicher-Init, Konfiguration)
   │  (signiert, redundant gespeichert)                          🔎
   ▼
3. Package1 / Secure Monitor (EL3, TrustZone)                    🔎/❓
   ▼
4. Package2: Horizon-Kernel + Kern-Sysmodules                    🔎
   ▼
5. Restliche Systemdienste, HOME-Menü, Spiele
```

- **PSC (Platform Security Controller):** In neueren NVIDIA-Tegra-Chips gibt es einen getrennten Sicherheitsprozessor, der Schlüssel verwaltet und Boot-Stufen prüft. Er ersetzt in etwa den TSEC (Falcon) der Switch 1 (🔎/❓).
- Laut Community-Analysen wird der Power-Management-Prozessor auf der Switch 2 als **nicht vertrauenswürdig** behandelt. Bei der Switch 1 war er ein Angriffsweg (❓).

## 4. eFuses (einmal programmierbare Sicherungen)

Die Fuses sind winzige Sicherungen im SoC, die nur **einmal** von 0 auf 1 gebrannt werden können.

- Sie speichern u. a. den **Hash des öffentlichen Boot-Schlüssels**, den **Production-Mode** und gerätespezifische Werte.
- **Redundanz (🔎 Switchbrew):** Die ersten 80 Fuse-Wörter liegen als 40 redundante Paare vor. Beide Werte müssen übereinstimmen. Das erschwert es, durch gezielte Störungen (Glitching) einen Fuse-Wert falsch auszulesen.
- **Anti-Downgrade:** Bei der Switch 1 wurden bei wichtigen Updates Fuses gebrannt. Ein Boot mit älterer Firmware schlägt dann fehl. Für die Switch 2 ist dasselbe Prinzip sehr wahrscheinlich (❓).

## 5. Schlüssel & Kryptografie

- Gerätespezifische Schlüssel werden in der Sicherheits-Hardware abgeleitet und liegen **nie im Klartext im RAM** (🔎 Prinzip von Switch 1).
- Spiele und Apps können Krypto-Operationen nur indirekt über den Secure Monitor anfordern (`spl`-Dienst).
- **Speicherverschlüsselung:** Die System- und Benutzer-Partitionen auf dem UFS sind verschlüsselt (bei der Switch 1 AES-XTS mit gerätespezifischen „BIS-Keys“) (🔎).
- **Inhalte (NCA):** verschlüsselt **und** signiert. Manipulierte Dateien werden beim Laden abgelehnt.
- **microSD:** Inhalte auf der SD-Karte sind an die Konsole gebunden verschlüsselt (🔎).

## 6. Laufzeit-Schutz im Betriebssystem

| Mechanismus | Wirkung |
|---|---|
| **Mikrokernel + Sandbox** | Jeder Dienst und jedes Spiel ist ein isolierter Prozess mit eigenem Adressraum |
| **Rechte-Deklaration (NPDM/ACID)** | Ein Programm darf nur die Syscalls und Dienste nutzen, die in seinen signierten Metadaten stehen |
| **Code-Signatur beim Laden** | Der Loader prüft ausführbare Dateien; es gibt keinen Weg, unsignierten Code nachzuladen |
| **W^X / NX** | Speicher ist entweder beschreibbar oder ausführbar, nie beides (kein JIT für Spiele) |
| **ASLR** | Zufällige Speicheradressen erschweren Exploits |
| **Moderne ARM-Schutzmaßnahmen** | ARMv8.2 (A78C) ermöglicht z. B. PAN/UAO. Ob Nintendo Pointer Authentication oder ähnliches nutzt, ist nicht öffentlich bekannt (❓) |

## 7. Lizenzen & Game Cards

- **eTickets (`es`-Dienst):** Digitale Käufe sind über ein **Ticket** an Nintendo-Account und Konsole gebunden.
- **Virtual Game Cards:** Die Lizenz wird serverseitig einer Konsole zugeordnet. Beim „Umstecken“ wird sie online zwischen Konsolen verschoben (✅ Funktion, Mechanismus 🔎).
- **Game Cards:** Der Game-Card-Controller authentifiziert die Karte kryptografisch, bevor Inhalte gelesen werden (bei der Switch 1 über den Lotus3-Chip, 🔎. Für die Switch 2 ist ein vergleichbares Verfahren anzunehmen, ❓).
- Jede Game Card hat eine **eindeutige Kennung bzw. ein Zertifikat**. Das ermöglicht es Nintendo, kopierte Karten online zu erkennen.

## 8. Online-Schutz & Sperren

- Die Konsole meldet sich mit einem **Gerätezertifikat** bei Nintendos Servern an (🔎).
- Nintendo erkennt auffällige Muster serverseitig, z. B. dieselbe Game-Card-Kennung auf vielen Konsolen.
- **Praxisbeispiel (✅ medial berichtet, Juni 2025):** Nutzer von „MIG Switch“-Flashkarten (Kopien von Switch-1-Spielen) wurden auf der Switch 2 kurz nach dem Start **online gesperrt**.
- **Nutzungsbedingungen (✅):** Nintendo hat 2025 die Bedingungen so geändert, dass bei unautorisierten Modifikationen oder Raubkopien die Konsole „ganz oder teilweise dauerhaft unbrauchbar“ gemacht werden darf.

## 9. Stand der Sicherheitsforschung (Oktober 2026)

| Datum | Ereignis | Verlässlichkeit |
|---|---|---|
| Juni 2025 | Erste **Userland-Exploits** (ROP in einem Spiel) öffentlich demonstriert, ohne Kernel- oder Bootzugriff | 🔎 |
| Juli 2026 | **Gezine-Exploit**: universeller Userland-Exploit, offline, auf allen Firmware-Versionen, bleibt in der Sandbox | 🔎 |
| Okt. 2026 | **„ns2jb“** (Forscher: pepsipu) für Systemversion **23.0.1**: softwarebasierter, **tethered** Jailbreak, der nach jedem Neustart erneut ausgelöst werden muss | 🔎 Kotaku; Umfang umstritten |
| Okt. 2026 | Behauptungen über einen vollständigen Firmware-Dump und einen PC-Emulator | ❓ **nicht verifiziert** |
| – | **Kein** bekannter BootROM-Exploit, keine permanente Custom Firmware, kein bestätigter Modchip | Stand der Berichte |

Fazit: Die Switch 2 ist deutlich besser abgesichert als die Switch 1. Die Kette BootROM → PSC → signierte Stufen gilt bisher als ungebrochen. Bekannte Angriffe setzen im Userland bzw. Systembereich an und lassen sich per Update schließen.

## Quellen

- [Switchbrew – Switch 2: Fuses](https://switchbrew.org/wiki/Switch_2:_Fuses)
- [Switchbrew – Fuses (Switch 1)](https://switchbrew.org/wiki/Fuses)
- [Switchbrew – Switch System Flaws](https://switchbrew.org/wiki/Switch_System_Flaws)
- [SwitchTools – UFS-LUNs und Boot-Stufen (X)](https://x.com/SwitchTools/status/1937118212933439514)
- [GBAtemp – Switch-2-Härtung gegen RCM/Glitching (Forum)](https://gbatemp.net/threads/let-me-save-you-the-suspense-the-switch-2-wont-get-hacked.676435/)
- [GBAtemp – Modchip-Angriffsvektoren (Forum)](https://gbatemp.net/threads/switch-2-data-gathering-for-possible-modchip-attack-vectors.668520/)
- [Kotaku – The Switch 2 Has Been Jailbroken For The First Time](https://kotaku.com/nintendo-switch-2-jailbreak-hack-exploit-piracy-homebrew-emulation-modding-2000748784)
- [Techyorker – Was ns2jb tatsächlich beweist](https://techyorker.com/switch-2-firmware-dump-23-0-1-what-the-ns2jb-exploit-actually-proves-and-why-theres-no-emulator/)
- [Wayayeo – Modding-Stand August 2026](https://wayayeo.org/nintendo-switch-2-modding-early-homebrew-and-hack-news/)
