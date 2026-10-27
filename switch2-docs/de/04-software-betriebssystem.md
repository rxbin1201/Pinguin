# Software: Betriebssystem „Horizon“

> Hinweis: Nintendo dokumentiert das System nicht öffentlich. Vieles ist von der Switch 1 bekannt (Switchbrew-Wiki) und gilt nach bisherigen Analysen weitgehend auch für die Switch 2 (🔎). Wo es Unterschiede gibt oder nichts bekannt ist, steht ❓.

## 1. Grundprinzip: Mikrokernel

Die Switch 2 läuft auf **Horizon**, einem von Nintendo selbst entwickelten Betriebssystem. Es ist **kein Linux und kein Android**. Horizon stammt ursprünglich vom 3DS und wurde für die Switch neu geschrieben.

- **Mikrokernel:** Der Kernel macht nur das Nötigste: Threads, Speicherverwaltung, Interrupts, Synchronisation und Interprozesskommunikation (IPC).
- **Alles andere sind Prozesse im Userland:** Dateisystem, Treiber, Netzwerk, Eingabe usw. laufen als eigene, isolierte **Sysmodules**.
- Vorteil: Stürzt ein Dienst ab oder wird er kompromittiert, bekommt ein Angreifer nicht automatisch Kernel-Rechte.

## 2. Privilegienstufen (ARMv8 Exception Levels)

| Ebene | Was läuft dort | Quelle |
|---|---|---|
| EL3 | **Secure Monitor** (TrustZone): Schlüsselzugriff, Power-Management-Aufrufe, sensible Kryptografie | 🔎 (Switch 1) / ❓ Details Switch 2 |
| EL2 | Bei der Switch 1 ungenutzt (kein Hypervisor). Für Switch 2 unklar. | ❓ |
| EL1 | **Horizon-Kernel** | 🔎 |
| EL0 | Sysmodules, Applets, Spiele | 🔎 |

## 3. Wichtige Systemdienste (Sysmodules)

Die Dienste sprechen über IPC miteinander. Ein Prozess fragt beim **Service Manager (`sm`)** nach einem Dienst, z. B. `fsp-srv`, und bekommt eine **Session**, über die er Anfragen schickt.

| Dienst | Aufgabe |
|---|---|
| `sm` | Service Manager: registriert Dienste und prüft, ob ein Prozess sie benutzen darf |
| `pm` | Process Manager: startet und beendet Prozesse |
| `ldr` | Loader: lädt ausführbare Dateien (NSO), prüft Signaturen |
| `fs` | Dateisystem: UFS, microSD, Game Cards, Entschlüsselung von Inhalten |
| `ncm` | Content Manager: verwaltet installierte Inhalte |
| `ns` | Nintendo Shell: Anwendungsverwaltung, Starten von Spielen |
| `am` | Applet Manager: HOME-Menü, Fokus, Suspend |
| `hid` | Eingabe: Joy-Con, Touch, Maus-Sensor |
| `nvservices` | NVIDIA-GPU-Treiber (Userland) |
| `audio` | Audio-Ausgabe |
| `bsdsockets`, `nifm`, `ssl` | Netzwerk, Verbindungsverwaltung, TLS |
| `account` | Nutzerkonten / Nintendo Account |
| `es` | **eTicket Service**: Lizenzen (Tickets) für digitale Spiele |
| `nim` | Download/Installation aus dem eShop, Systemupdates |
| `spl` / `csrng` | Zugriff auf Krypto- und Zufallsfunktionen des Secure Monitors |

(Liste nach Switch-1-Architektur, 🔎. Die Switch 2 hat zusätzliche Dienste, z. B. für GameChat, Kamera, Maus-Eingabe und Game-Key-Cards ❓.)

## 4. Applets und Spiele

- **System-Applets:** HOME-Menü (`qlaunch`), Overlay (Schnellmenü), Einstellungen, eShop, Album, Nutzerauswahl usw.
- **Anwendungen:** Spiele laufen als eigene Prozesse in einer Sandbox. Sie dürfen nur auf die Dienste zugreifen, die in ihren Metadaten (NPDM) erlaubt und von Nintendo signiert sind.
- **Grafik:** Spiele nutzen **NVN2** direkt (sehr hardwarenah) und können DLSS und Raytracing einsetzen.

## 5. Dateiformate & Inhalte (🔎, von Switch 1 übernommen)

| Format | Bedeutung |
|---|---|
| **NCA** | Nintendo Content Archive: verschlüsselter, signierter Container für Programmcode, Daten und Metadaten |
| **NSO** | ausführbares Format (komprimiertes ELF-Derivat) |
| **NPDM** | Programm-Metadaten: Rechte, erlaubte Dienste, Syscalls |
| **Ticket** | Lizenz für digitale Inhalte (an Konto/Konsole gebunden) |

## 6. Updates & Versionsnummern

- Switch 1 und Switch 2 teilen sich die Versionsnummern-Reihe. Die Switch 2 startete mit **Systemversion 20.x** (🔎). Im Herbst 2026 ist der Stand 23.x (🔎).
- Updates werden signiert ausgeliefert und kommen über das Internet oder auf Game Cards.
- Nach Updates werden zum Teil **Fuses** gebrannt, sodass eine ältere Version nicht mehr installiert werden kann (Anti-Downgrade, siehe [05-sicherheit.md](05-sicherheit.md)).

## 7. Abwärtskompatibilität zu Switch 1

- Die meisten Switch-1-Spiele laufen auf der Switch 2 (✅). Nintendo pflegt eine Liste von Ausnahmen.
- **CPU-Code:** A57 und A78C sind beide ARMv8. Der Code läuft daher nativ.
- **GPU-Code:** Switch-1-Spiele enthalten fertig kompilierte **Maxwell-Shader**. Ampere versteht diese nicht direkt. Die Switch 2 nutzt daher eine **Übersetzungsschicht**, die Shader und GPU-Befehle für Ampere umsetzt (🔎). Deshalb gibt es manche Grafikfehler und inkompatible Titel.
- **„Nintendo Switch 2 Edition“** und kostenlose Updates bieten bei manchen Switch-1-Spielen native Verbesserungen (✅).

## 8. Neue Software-Funktionen

| Funktion | Beschreibung | Quelle |
|---|---|---|
| **GameChat** | Sprach- und Video-Chat, Bildschirm teilen, ausgelöst über die C-Taste | ✅ |
| **Virtual Game Cards** | Digitale Spiele lassen sich zwischen zwei Konsolen „umstecken“ und innerhalb einer Familiengruppe verleihen | ✅ |
| **Game-Key-Cards** | Physische Karte als Lizenz, das Spiel wird heruntergeladen | ✅ |
| **Maus-Steuerung** | Neue `hid`-Eingabeart über den Joy-Con-2-Sensor | ✅ / 🔎 (Dienst) |
| **Jugendschutz** | Erweiterte Kindersicherung inkl. GameChat-Freigabe per App | ✅ |

## Quellen

- [Switchbrew (Switch-1-Dokumentation, Basis vieler Angaben)](https://switchbrew.org/wiki/Main_Page)
- [Switchbrew – Boot2](https://switchbrew.org/wiki/Boot2)
- [Wikipedia – Nintendo Switch 2](https://en.wikipedia.org/wiki/Nintendo_Switch_2)
- [SwitchTools – Zusammenfassung Switch-2-Software (X)](https://x.com/SwitchTools/status/1937118212933439514)
