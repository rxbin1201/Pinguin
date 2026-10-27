# USB-Beobachtungen: Switch 2 direkt am PC

Eigene Messung vom **2026-10-27** mit [usb_probe.py](../../switch2-tools/usb_probe.py) (passiv, nur GET_DESCRIPTOR).

## 1. Versuchsaufbau

| | |
|---|---|
| Konsole | Nintendo Switch 2 (Retail) |
| Anschluss | **unterer USB-C-Port** der Konsole → USB-Port des PCs (direkt, ohne Dock) |
| Host | Windows-PC, pyusb + libusb |
| Ablauf | Logger gestartet, danach Konsole verbunden bzw. gebootet |
| Rohdaten | `boot1.jsonl` (enthält die Seriennummer, nicht öffentlich teilen) |

> Hinweis: `t_rel` misst die Zeit ab Start des Loggers, nicht ab Einschalten der Konsole. Der genaue Abstand zum Einschalten wurde nicht festgehalten.

## 2. Ergebnis auf einen Blick

- Die Konsole meldet sich **ein einziges Mal** als USB-Gerät an (bei t = 6,79 s). Es gibt **keine Zwischenstufen** während des Bootens: kein zweites Gerät, kein NVIDIA-Recovery-Gerät (`0955:xxxx`), kein Wechsel der Kennung.
- Die Konsole verhält sich als **USB-Gerät** (Device), der PC als Host.
- Sichtbar ist **nur eine minimale HID-Schnittstelle** mit einem einzigen 1-Byte-Endpoint (Konsole → PC). Es gibt **keine** Massenspeicher-, MTP- oder Hersteller-Schnittstelle.
- Der Report ist immer `0x00` und kommt alle 4 ms, weil die Switch `SET_IDLE` ablehnt (6.5, 6.6).
- Eine **ausgeschaltete** Konsole fährt beim Einstecken des Kabels **automatisch hoch** und meldet sich nach konstant ~6,3 s an (eingeschaltet: ~0,7 s) (6.6, 6.7).

## 3. Geräte-Deskriptor

| Feld | Wert | Bedeutung |
|---|---|---|
| VID:PID | **`057e:2060`** | `057e` = Nintendo, `2060` = Produkt-ID der Switch 2 in diesem Modus |
| Hersteller (String) | `Nintendo` | |
| Produkt (String) | `Nintendo Switch 2` | |
| Seriennummer (String) | `HAE1058xxxxxxx` (gekürzt) | entspricht vermutlich der Konsolen-Seriennummer (mit Aufkleber/Einstellungen abgleichen) |
| bcdUSB | 2.00 | meldet sich als **USB 2.0**-Gerät |
| Geschwindigkeit | High Speed (480 Mbit/s) | obwohl USB-C, keine SuperSpeed-Verbindung |
| bcdDevice | 1.00 | Geräte-Revision |
| Geräteklasse | 0x00 | Klasse wird pro Interface angegeben |
| bMaxPacketSize0 | 64 | Standard für High Speed |
| Configurations | 1 | |
| BOS-Deskriptor | keiner | bei USB 2.00 nicht vorgesehen (erst ab 2.01) |

## 4. Configuration, Interface, Endpoint

```
Configuration 1
  bmAttributes = 0xC0  → selbstversorgt (self-powered), kein Remote Wakeup
  bMaxPower    = 50    → 50 × 2 mA = 100 mA (zieht kaum Strom vom Bus)
  └─ Interface 0, Alt 0
       Klasse   0x03 HID
       Subklasse 0x00 (kein Boot-Gerät, also keine Tastatur/Maus im BIOS-Sinne)
       Protokoll 0x00
       └─ Endpoint 0x81
            Richtung  IN (Konsole → PC)
            Typ       Interrupt
            MaxPacket 1 Byte
            bInterval 10 → bei High Speed 2^(10−1) × 125 µs = 64 ms
```

## 5. Interpretation

| Beobachtung | Deutung | Sicherheit |
|---|---|---|
| Nur ein HID-Interface mit 1 Byte, nur IN, alle 64 ms abfragbar | Sehr wahrscheinlich eine **minimale „Platzhalter“- bzw. Statusschnittstelle**. HID braucht unter Windows, macOS und Linux keinen Treiber. Das Gerät erscheint also sauber im System, ohne Fehlermeldung „Treiber nicht gefunden“. Abschnitt 6 bestätigt das. | 🔎 durch Messung gestützt |
| Kein OUT-Endpoint | Der PC kann über diese Schnittstelle **keine Daten an die Konsole senden** (außer über Standard-Control-Requests an EP0) | ✅ aus Deskriptor |
| Keine MTP-/Massenspeicher-Schnittstelle | Im normalen Betrieb **kein Dateizugriff** (z. B. Screenshots) über USB, zumindest nicht in diesem Zustand | ✅ für diesen Zustand |
| Self-powered, 100 mA | Die Konsole versorgt sich selbst (Akku) und fordert über USB-Daten praktisch keinen Strom an. Laden läuft separat über USB-C/PD. | ✅ aus Deskriptor |
| USB 2.0 statt 3.x | Die SuperSpeed-Leitungen sind für den **DisplayPort-Alt-Mode** im Dock vorgesehen. Für Daten zum PC wird nur USB 2.0 genutzt. | 🔎 plausibel |
| Kein Gerät vor dem eigentlichen Anmelden | Während des Bootens ist **kein Recovery- oder Bootloader-USB-Gerät** sichtbar (anders als beim RCM-Modus der Switch 1, `0955:7321`) | ✅ für diesen Durchlauf |
| Seriennummer im USB-String | Die Konsole gibt ihre Seriennummer an jeden angeschlossenen Host weiter | ✅ |

## 6. HID-Analyse (zweiter Durchlauf)

Messung mit [hid_probe.py](../../switch2-tools/hid_probe.py) (hidapi, passiv), Rohdaten `hid1.jsonl`.

### 6.1 Report-Deskriptor (26 Bytes)

> **Korrektur:** In der ersten Fassung stand hier eine 24-Byte-Version aus `hidapi`. Unter Windows liest hidapi den Deskriptor nicht roh aus, sondern **baut ihn aus den Daten des Windows-HID-Treibers nach**. Dabei fiel das doppelte `05 06` weg. Der USBPcap-Mitschnitt (6.6) zeigt den echten Deskriptor mit **26 Bytes**. Inhaltlich ändert sich nichts.

```
05 06            Usage Page (Generic Device Controls)
09 20            Usage (0x20 = Battery Strength)
a1 01            Collection (Application)
09 20              Usage (Battery Strength)
a1 00              Collection (Physical)
05 06                Usage Page (Generic Device Controls)   ← fehlt in der hidapi-Version
09 20                Usage (Battery Strength)
15 81                Logical Minimum (-127)
25 7f                Logical Maximum (127)
75 08                Report Size (8)
95 01                Report Count (1)
81 06                Input (Data, Variable, Relative)
c0                 End Collection
c0               End Collection
```

- Ein einziger Input-Report: **1 Byte, ohne Report-ID**. Es gibt **keine Output- und keine Feature-Reports**. Über HID kann der PC der Konsole also nichts schicken.
- Die Usage `0x06:0x20` heißt laut *HID Usage Tables* **„Battery Strength“**.
- **Das passt nicht zusammen:** Ein Akkustand wäre ein absoluter Wert (z. B. 0–100 bzw. 0–255). Hier ist der Wert aber als **relativ und vorzeichenbehaftet (−127…127)** deklariert. Ein relativer Wert von 0 bedeutet nach HID-Logik „keine Änderung“, das Betriebssystem ignoriert ihn also.

### 6.2 Zeitverlauf

Die Markierungen wurden jeweils **nach** der Aktion eingetippt (ca. 4–5 s Verzögerung). Die Zuordnung ergibt sich aus dem zeitlichen Muster.

| t (s) | Ereignis | Zuordnung |
|---|---|---|
| 10,5 | Anmeldung, Report `00` | Konsole verbunden |
| 41,8 | Markierung `home-menue` | keine Änderung |
| 84,7 | Markierung `spiel-gestartet` | keine Änderung |
| 92,3 | **Abmeldung** | Konsole geht in den Schlafmodus |
| 97,6 | Markierung `schlafmodus` | (nachgetragen) |
| 98,1 | **Neue Anmeldung**, gleicher Deskriptor | Konsole meldet sich **im Schlafmodus** neu an |
| 105,6 | Markierung `aufgewacht` | **keine** Ab- oder Neuanmeldung beim Aufwachen |
| 115,8 | Markierung `einstellungen` | keine Änderung |
| 118,9 | **Abmeldung** | Kabel abgezogen |
| 123,4 | Markierung `kabel-ab` | (nachgetragen) |
| 126,4 | **Neue Anmeldung** | Kabel eingesteckt |
| 130,6 | Markierung `kabel-dran` | (nachgetragen) |

### 6.3 Ergebnisse

| Beobachtung | Details |
|---|---|
| **Byte ist immer `0x00`** | In allen Zuständen (HOME-Menü, Spiel, Schlafmodus, Einstellungen, nach dem Neuverbinden) |
| **Report-Rate ~250/s (alle 4 ms)** | konstant 2476–2506 Reports pro 10 s, auch **während des Schlafmodus**. Laut Endpoint-Deskriptor wären 64 ms (~16/s) zu erwarten. Per USBPcap bestätigt, siehe 6.5. |
| **Schlafmodus = Neu-Anmeldung** | Beim Einschlafen meldet sich das Gerät ab und nach ~5,7 s wieder an (gleiche Kennung, gleicher Deskriptor). Im Schlafmodus bleibt es aktiv und sendet weiter. |
| **Aufwachen ohne USB-Ereignis** | Das USB-Gerät bleibt beim Aufwachen unverändert bestehen |
| **Kabel ab/an** | normales Ab- und Anmelden, ~7,5 s Pause (manuell) |

### 6.4 Deutung

Die Schnittstelle trägt **keine Nutzdaten**: Das Byte ist konstant 0, und als „relative“ Angabe bedeutet 0 nach HID-Logik ohnehin „nichts passiert“. Am plausibelsten ist eine **Dummy- bzw. Platzhalter-HID-Schnittstelle** (❓ Hypothese):

- **HID braucht keinen Treiber.** Jedes Betriebssystem erkennt das Gerät sauber, ohne Meldung „Unbekanntes Gerät“.
- **Die gewählte Usage ist harmlos.** Battery Strength unter Generic Device Controls wird nicht als Tastatur, Maus oder Gamecontroller eingebunden. Die Konsole löst am PC also keine Eingaben aus.
- **Mögliche Zwecke** (alle ❓): Der PC soll eine Datenverbindung erkennen, damit z. B. Strom und Port-Rolle stabil bleiben. Oder die Schnittstelle dient als Anwesenheitssignal für Nintendo-eigene Werkzeuge (Werkstatt/Service) bzw. als Grundlage für spätere Funktionen.

Dass sich die Schnittstelle im Schlafmodus neu anmeldet, deutet darauf hin, dass der USB-Device-Teil beim Einschlafen neu initialisiert wird. Er läuft dann vermutlich in einem stromsparenden Zustand des SoC weiter (❓).

### 6.5 USBPcap-Mitschnitt (dritter Durchlauf)

Mitschnitt mit USBPcap am Root-Hub des AMD-Chipsatz-Controllers (`1022:43EE`), ausgewertet mit [usb_pcap_analyze.py](../../switch2-tools/usb_pcap_analyze.py). Während der Aufnahme wurde das Kabel einmal ab- und wieder angesteckt. Deshalb kommt die Switch unter zwei Adressen vor:

| Adresse | Sitzung | Interrupt-IN-Completions | Bemerkung |
|---|---|---|---|
| 19 | vor dem Abziehen | 1098 in 4,38 s | endet mit `CANCELED` (Transfer beim Abziehen abgebrochen) und einmal `INVALID_PARAMETER` |
| 20 | nach dem Einstecken | ~10.900 | komplette Anmeldung im Mitschnitt (24 Control-Pakete) |

**Messwerte Adresse 19:**

| Wert | Ergebnis |
|---|---|
| Rate | **250,0 Reports/s** |
| Abstand Median | **4,000 ms** |
| Abstand p5 / p95 | 3,993 / 4,008 ms |
| Abstand min / max | 3,695 / 4,277 ms |
| Payload | 1096× `00`, kein anderer Wert |

**Ergebnis:** Die 4 ms sind **kein Messfehler von hidapi**. USBPcap sieht die Antworten des Treibers direkt: Jede Anfrage wird mit Daten beantwortet, und zwar sehr gleichmäßig alle 4 ms.

**Deutung:**
- **Host-Seite:** Windows bzw. der AMD-xHCI-Controller fragt den Endpoint alle 4 ms ab statt alle 64 ms, wie es `bInterval = 10` vorsieht. Wie oft abgefragt wird, entscheidet allein der Host. Die Ursache liegt also im Windows-USB-Stack oder im Controller, nicht in der Switch (❓ genauer Grund offen).
- **Geräte-Seite:** Bemerkenswert ist, dass die Switch auf **jede** Abfrage mit einem Report antwortet, obwohl sich der Wert nie ändert. Ein typisches HID-Gerät antwortet mit NAK, wenn es nichts Neues gibt (Idle-Rate 0), und der Treiber bekommt dann nichts. Die Switch hält offenbar immer einen Report bereit. Grund: Die Switch lehnt `SET_IDLE` ab (siehe 6.6).

### 6.6 Anmeldung im Detail (vierter Durchlauf)

Ablauf: **Switch ausgeschaltet**, Mitschnitt gestartet, Kabel eingesteckt. Ausgewertet ist Adresse 21.

| t (ms) | Request | Antwort |
|---|---|---|
| 0,0 | `GET_DESCRIPTOR` Device (18) | OK, `057e:2060`, USB 2.00 |
| 2,7 | `GET_DESCRIPTOR` Configuration (9) | OK, Gesamtlänge 34 Bytes |
| 5,8 | `GET_DESCRIPTOR` Configuration (34) | OK, Config + Interface + HID-Deskriptor + Endpoint |
| 8,7 | `SET_CONFIGURATION` 1 | OK |
| 14,1 | **`SET_IDLE` (Idle-Rate 0)** | **STALL** → wird von der Switch **abgelehnt** |
| 16,0 | `GET_DESCRIPTOR` Report (angefragt 90) | OK, **26 Bytes** |
| 592 / 595 | `GET_DESCRIPTOR` String #2 (Produkt) | OK, 36 Bytes = „Nintendo Switch 2“ (17 Zeichen) |
| 2578 / 2581 | String #2 erneut | OK, gleiche Antwort |

**Erkenntnisse:**

1. **`SET_IDLE` wird mit STALL abgelehnt.** Mit `SET_IDLE` und Idle-Rate 0 bittet Windows ein HID-Gerät, nur bei Änderungen zu senden. Laut HID-Spezifikation dürfen Geräte, die keine Boot-Geräte sind, diesen Request ablehnen. Die Switch tut das und **sendet deshalb bei jeder Abfrage** ihren Report. Das erklärt die Geräte-Seite der 4-ms-Beobachtung aus 6.5.
2. **Report-Deskriptor:** Windows fragt 90 Bytes an (Länge aus dem HID-Deskriptor + 64 Bytes Puffer, so macht es Windows bei HID immer). Die Switch liefert 26 Bytes, das korrigiert 6.1.
3. **HID-Deskriptor in der Configuration:** `09 21 11 01 00 01 …` = HID-Version **1.11**, Ländercode 0, **ein** Unterdeskriptor (Report). Ein Physical-Deskriptor ist nicht vorhanden.
4. **Kein String-Request für die Seriennummer** und kein `SET_ADDRESS` im Mitschnitt: Diese ersten Schritte erledigt der Hub-Treiber unterhalb von USBPcap. Sie sind mit dieser Methode **nicht sichtbar**. Windows hat die Seriennummer trotzdem, siehe die Geräte-ID.
5. **Report-Rate wie zuvor:** 247,8/s, Median 4,000 ms, nur Werte `00`. 7 von 3237 Abständen lagen über 5 ms (max. 72 ms), vermutlich kurze Pausen beim Scheduling des Hosts.
6. **Eine ausgeschaltete Switch schaltet sich beim Einstecken des Kabels selbst ein.** Die Konsole war über *Power-Taste halten → „Ausschalten“* heruntergefahren. Wird ein USB-Kabel zum PC eingesteckt, **fährt sie automatisch hoch**. Das USB-Gerät stammt also aus dem **normal gestarteten System**, nicht aus einem eigenen Lade- oder Standby-Modus. Gerät, Deskriptoren, `SET_IDLE`-STALL und die 4-ms-Reports sind entsprechend **identisch** zum eingeschalteten Zustand.
   - > **Korrektur:** Eine frühere Fassung vermutete hier einen „Lademodus mit minimaler Firmware“. Das ist durch die Beobachtung des automatischen Hochfahrens überholt.
   - **Datenschutz:** Steckt man die ausgeschaltete Konsole an einen fremden USB-Port (z. B. eine öffentliche Ladestation), fährt sie hoch und gibt dabei ihre **Seriennummer** preis. Über HID ist dabei nur dieselbe minimale Schnittstelle sichtbar (ein Interface, ein IN-Endpoint, keine Output-/Feature-Reports, `SET_IDLE` wird abgelehnt).

### 6.7 Zeit vom Einstecken bis zur Anmeldung (fünfter Durchlauf)

Messung mit [usb_probe.py](../../switch2-tools/usb_probe.py): Beim Einstecken des Kabels an der Switch wurde Enter gedrückt, das Skript misst die Zeit bis zur Anmeldung. Je 3 Durchläufe, Rohdaten `timing.jsonl`.

| Zustand | Lauf 1 | Lauf 2 | Lauf 3 | Mittel |
|---|---|---|---|---|
| **eingeschaltet** | 0,55 s | 0,76 s | 0,72 s | **0,68 s** |
| **ausgeschaltet** („Ausschalten“, vor jedem Lauf neu heruntergefahren) | 6,28 s | 6,31 s | 6,32 s | **6,30 s** |

- In allen 6 Läufen waren die Deskriptoren **identisch** (gleiche Kennung, gleiche Schnittstelle, High Speed, gleicher Port).
- Messungenauigkeit: Reaktionszeit beim Enter-Drücken plus 100 ms Abfrageintervall des Skripts, zusammen etwa ±0,2 s.

**Ergebnis:** Im ausgeschalteten Zustand dauert die Anmeldung **rund 5,6 s länger**, und das **auffallend gleichmäßig** (Streuung nur ±0,02 s).

**Deutung:**
- Das Einstecken schaltet die Konsole ein (siehe 6.6, Punkt 6). Die **6,3 s** sind also die Zeit **vom Einschalten bis zu dem Moment im Bootvorgang, in dem der USB-Device-Teil aktiv wird**. Darin stecken die USB-PD-Aushandlung, die Boot-Kette (BootROM → signierte Stufen → Kernel) und der Start des zuständigen Systemdienstes.
- Die sehr geringe Streuung zeigt einen **deterministischen Bootablauf** bis zu diesem Punkt.
- **Vor** der Anmeldung nach 6,3 s erscheint **kein anderes USB-Gerät** (kein Bootloader-/Recovery-Gerät). Die frühen Bootstufen bieten über USB also nichts an (🔎 für diesen Aufbau).
- Im eingeschalteten Zustand läuft das System schon, die ~0,7 s sind die normale Anmeldung durch Windows.
- **Auffällige Parallele:** Beim Wechsel in den Schlafmodus (6.2) war die Switch für **~5,7 s** abgemeldet, bevor sie sich neu anmeldete. Das liegt in derselben Größenordnung wie die 5,6 s hier. Möglicherweise wird in beiden Fällen dieselbe Initialisierung des USB-Teils durchlaufen (❓ Vermutung).

**Nebenbeobachtung:** Nach einem **Neustart des PCs** hat sich die Switch nicht von selbst wieder als USB-Gerät angemeldet. Windows führte sie nur noch als nicht vorhanden. Erst nach dem Ab- und Anstecken des Kabels erschien sie wieder.

## 7. Offene Fragen / nächste Schritte

1. ~~HID-Report-Deskriptor auslesen~~ → erledigt, siehe 6.1.
2. ~~Input-Reports mitlesen~~ → erledigt: Wert konstant `0x00`.
3. ~~Report-Rate klären~~ → erledigt, siehe 6.5: 4 ms sind real.
   ~~Control-Requests der Anmeldung auswerten~~ → erledigt, siehe 6.6: `SET_IDLE` wird abgelehnt (STALL).
   **Offen:** Fragt ein Linux-Host ebenfalls alle 4 ms ab, oder ist das eine Eigenheit von Windows/AMD?
   ~~War die Konsole bei Durchlauf 4 komplett aus?~~ → ja, über „Ausschalten“ heruntergefahren.
   ~~Zeit vom Einstecken bis zur Anmeldung~~ → erledigt, siehe 6.7: an 0,68 s, aus 6,30 s.
   ~~Lademodus → Einschalten~~ → entfällt: Die Konsole fährt beim Einstecken automatisch hoch (6.6).
   **Offen:** Wie lange dauert der Boot bis zum HOME-Menü im Vergleich zu den 6,3 s bis zur USB-Anmeldung? Daraus ließe sich ablesen, wie früh im Bootvorgang der USB-Dienst startet.
4. **Zeitpunkt messen:** Logger starten, **dann** einschalten und den Moment notieren. So erfährt man, in welcher Boot-Phase die Anmeldung passiert.
5. **Oberen USB-C-Port** testen: gleiche Kennung oder anderes Verhalten?
6. **Weitere Zustände:** Konsole ganz aus (nur Laden), Neustart, Systemupdate, Datenübertragung, Album.
7. **Dock am PC** anschließen und Hub/LAN-Chip mit den Switchbrew-Angaben abgleichen.
8. **Power Delivery** (CC-Leitungen) mit einem Hardware-Sniffer mitschneiden: Dieser Teil ist mit Software allein nicht sichtbar.

## 8. Rohdaten (Auszug, Seriennummer gekürzt)

Die übrigen 12 Einträge im Log (`event: present`) sind Geräte des **PCs selbst** (Root-Hubs, interne Hubs, Bluetooth, Maus/Tastatur, USB-Stick usw.) und haben mit der Switch nichts zu tun.

```json
{"t_rel": 6.793, "event": "attach", "vid_pid": "057e:2060", "bus": 3, "address": 12,
 "device": {"speed": "High (480 Mbit/s)", "bcdUSB": "2.00", "bcdDevice": "1.00",
  "class": "0x00 (per-interface)", "max_packet_ep0": 64, "num_configurations": 1,
  "manufacturer": "Nintendo", "product": "Nintendo Switch 2", "serial": "HAE1058xxxxxxx",
  "configurations": [{"value": 1, "attributes": "0xc0", "max_power_raw": 50,
   "interfaces": [{"number": 0, "alt_setting": 0, "class": "0x03 (HID)",
    "subclass": "0x00", "protocol": "0x00",
    "endpoints": [{"address": "0x81", "direction": "IN", "type": "interrupt",
                   "max_packet": 1, "interval": 10}]}]}],
  "bos": null}}
```
