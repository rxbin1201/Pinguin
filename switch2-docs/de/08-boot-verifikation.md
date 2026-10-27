# Boot- und Signaturprüfung im Detail

> Dieses Kapitel **erklärt**, wie die Switch 2 bei jedem Start prüft, dass nur von Nintendo signierter Code läuft. Es ist keine Anleitung zum Umgehen dieser Prüfungen.
>
> **Quelle ist öffentliche Reverse-Engineering-Dokumentation** (v. a. das Switchbrew-/Switch2brew-Wiki), nicht die eigene Konsole. Über USB ist von diesen Prüfungen nichts zu sehen: Wie in [07](07-usb-beobachtungen.md) gemessen, meldet sich die Konsole erst nach ~6,3 s an, erst wenn der Boot schon weit fortgeschritten ist. Die frühen Stufen bieten nach außen nichts an.
>
> Vieles ist von der Switch 1 gut dokumentiert und für die Switch 2 nur teilweise bestätigt. Markierung: 🔎 aus RE-Doku, ❓ unbestätigt / von Switch 1 abgeleitet.

## 1. Grundidee: Chain of Trust

Jede Stufe prüft die **Signatur** der nächsten Stufe, bevor sie diese startet. Eine Signatur ist eine mathematische Unterschrift: Nintendo signiert mit einem **geheimen privaten Schlüssel**, die Konsole prüft mit dem zugehörigen **öffentlichen Schlüssel**. Den privaten Schlüssel hat nur Nintendo.

```
BootROM  ──prüft──►  erste Stufe  ──prüft──►  nächste Stufe  ──prüft──►  …
 (im Chip,            (PSC/MB1,               (Secure Monitor,
  unveränderbar)       auf dem UFS)            Kernel, …)
```

Der **Vertrauensanker** ist das BootROM: fest im SoC verdrahtet, nicht updatebar, und in den eFuses steht der Hash des öffentlichen Schlüssels, gegen den geprüft wird. Damit kann niemand einfach einen eigenen öffentlichen Schlüssel unterschieben, denn dessen Hash stünde nicht in den Fuses.

## 2. Was eine Signaturprüfung konkret tut

Am Beispiel einer Boot-Stufe:

1. Die Stufe liegt als Datei auf dem UFS, zusammen mit einer Signatur und (meist) verschlüsselt.
2. Die vorige Stufe berechnet einen **Hash** (eine Prüfsumme) über den Inhalt.
3. Sie prüft mit dem **öffentlichen Schlüssel**, ob die Signatur zu genau diesem Hash passt.
4. Nur wenn das stimmt, wird die Stufe entschlüsselt und ausgeführt. Sonst **Boot-Abbruch** (bei der Switch 1 mit einem Panic-Code).

Wichtig: Entschlüsselung und Signaturprüfung sind **zwei getrennte Dinge**. Die Verschlüsselung hält den Inhalt geheim, die Signatur stellt die Echtheit sicher. Beides muss stimmen.

## 3. Die erste Stufe: BR-BCT

Das BootROM lädt zuerst die **BCT** (Boot Configuration Table), hier **BR-BCT** genannt. Sie liegt ganz am Anfang der Boot-LUNs (LUN 0 und LUN 1) des UFS und sagt dem BootROM, wo die nächste Stufe liegt und wie sie geprüft wird.

Laut Switchbrew (Seite „Switch 2: BCT“, 🔎):

| Bereich | Inhalt |
|---|---|
| Offset 0x0 | Magic-Wert (Erkennung) |
| Signatur | **XMSS-SHA2_20_256** |
| Hash über 0x44–0x2000 | SHA-512 über fast die ganze Struktur |
| Hash über 0x1200–0x2000 | separater SHA-512 |
| BrBctHash über 0x170C–0x1AC0 | Hash über einen verschlüsselten Abschnitt |

### Der auffälligste Unterschied zur Switch 1

- **Switch 1:** RSA-2048 bzw. RSA mit PSS (klassische Public-Key-Kryptografie).
- **Switch 2:** **XMSS**, ein **hash-basiertes, quantencomputer-resistentes** Signaturverfahren.

XMSS (eXtended Merkle Signature Scheme) baut nur auf Hash-Funktionen auf. Das hat zwei Eigenschaften, die hier wichtig sind:

1. **Quantensicher:** RSA und ECC könnte ein künftiger Quantencomputer brechen, hash-basierte Verfahren nach heutigem Stand nicht. Für ein Gerät, das 10+ Jahre im Feld steht, ist das sinnvoll.
2. **Zustandsbehaftet:** XMSS hat eine begrenzte Zahl möglicher Signaturen (hier 2²⁰, also gut eine Million). Jeder private Schlüssel darf jede „Position“ nur **einmal** signieren. Das ist für Firmware, die selten signiert wird, unproblematisch, für Nintendo also gut handhabbar.

Dass Nintendo ausgerechnet die unterste, nicht updatebare Stufe quantensicher absichert, passt dazu, dass genau diese Stufe über die gesamte Lebensdauer halten muss.

## 4. Weitere Stufen: PSC, MB1, MBCT

Nach der BR-BCT folgen die frühen Stufen. Eine Community-Zusammenfassung (❓, unbestätigt) nennt:

- **MB1, PSC-Firmware, MBCT:** frühe Boot-Stufen, jeweils **signiert und redundant** auf den Boot-LUNs gespeichert.
- Eine Stufe-2 enthalte u. a. einen Zufalls-Salt, die **ECID** (gerätespezifische Chip-ID), eine Bindung an die BR-BCT und eine **RSA-3072**-Signatur für Stufe 1.

Das klingt nach einem **gemischten Ansatz**: XMSS für die unterste Verankerung, klassisches RSA (hier 3072 statt 2048 bei Switch 1) für spätere Stufen. Bestätigt ist das nicht.

**PSC (Platform Security Controller):** ein eigener kleiner Sicherheitsprozessor im SoC. In neueren NVIDIA-Tegra-Designs übernimmt er Schlüsselverwaltung und das Prüfen der Boot-Stufen. Er ersetzt in etwa den TSEC/Falcon der Switch 1. Wie der PSC selbst verifiziert wird, ist öffentlich nicht dokumentiert (❓).

## 5. Spätere Stufen: Secure Monitor, Kernel, Pakete

Ab hier ist die Switch 2 nur über die Switch-1-Doku abschätzbar (🔎 für Switch 1, ❓ für Switch 2):

- **Package1:** früher Bootloader-Teil plus Secure-Monitor-Code (läuft in TrustZone/EL3).
- **Package2:** der **Horizon-Kernel** plus die Kern-Sysmodules.

Bei der Switch 1 ist Package2 so aufgebaut:

| Bereich | Inhalt |
|---|---|
| Offset 0x0, 0x100 Bytes | **RSA-2048-Signatur**, PKCS#1 v2.1 **RSASSA-PSS** mit SHA-256 |
| danach | verschlüsselter Header |
| danach | verschlüsselter Body (AES-CTR, Schlüssel nur in TrustZone bekannt) |

Scheitert eine dieser Prüfungen, bricht der Boot ab. Switchbrew listet für die Switch 1 getrennte Panic-Codes für Fehler bei Signatur, Metadaten, Version und Payload von Package2 (🔎).

## 6. Anti-Downgrade über Fuses

Zusätzlich zur Signaturprüfung gibt es einen **Versionsschutz**:

- In den eFuses steht eine **Mindest-Firmwareversion** (Anti-Rollback-Zähler).
- Bei wichtigen Updates brennt die Konsole eine weitere Fuse und erhöht damit die Mindestversion.
- Eine ältere Firmware ist zwar **korrekt signiert**, ihre Version liegt aber unter dem Fuse-Zähler. Der Boot verweigert sie deshalb trotzdem.
- Gebrannte Fuses lassen sich physikalisch nicht zurücksetzen. Ein Downgrade auf eine ältere, eventuell angreifbare Version ist so dauerhaft blockiert.

Für die Switch 2 ist dieses Prinzip sehr wahrscheinlich (❓), die genauen Fuse-Zuordnungen stehen in Ansätzen auf der Switchbrew-Seite „Switch 2: Fuses“ (🔎). Die ersten 80 Fuse-Wörter liegen dort als 40 **redundante Paare** vor, was Glitching-Angriffe auf einzelne Fuse-Bits erschwert.

## 7. Warum man das von außen nicht „mitlesen“ kann

- Die Prüfungen laufen **im SoC**, in BootROM, PSC und TrustZone. Nichts davon wird über USB, Display oder einen anderen offenen Kanal ausgegeben.
- Schlüssel liegen in dedizierter Hardware und nie im Klartext im RAM, auf den normaler Code zugreifen kann.
- Deshalb ist die einzige seriöse Informationsquelle die **Analyse der öffentlich extrahierten Firmware durch die RE-Community**. Deren Ergebnisse stehen im Wiki, und dieses Kapitel fasst sie zusammen.

## 8. Bezug zur eigenen Firmware-Version

Die Konsole in diesem Projekt läuft noch auf der **Auslieferungs-Firmware** (keine Updates). Für die Boot-Verifikation heißt das:

- Der Anti-Downgrade-Zähler steht auf dem niedrigsten Stand, es wurden also noch keine zusätzlichen Fuses für neuere Versionen gebrannt.
- Die beschriebene Kette (BR-BCT mit XMSS → spätere Stufen → Secure Monitor → Kernel) ist dieselbe. Das Signaturverfahren ändert sich mit Updates nicht, nur die signierten Inhalte und der Mindestversions-Zähler.

## Quellen

- [Switchbrew – Switch 2: BCT](https://switchbrew.org/wiki/Switch_2:_BCT)
- [Switchbrew – BCT (Switch 1)](https://switchbrew.org/wiki/BCT)
- [Switchbrew – Package2](https://switchbrew.org/wiki/Package2)
- [Switchbrew – Package1](http://www.switchbrew.org/wiki/Package1)
- [Switchbrew – Panic codes](https://switchbrew.org/w/index.php?title=Panic_codes&mobileaction=toggle_view_desktop)
- [Switchbrew – Switch 2: Fuses](https://switchbrew.org/wiki/Switch_2:_Fuses)
- [Switchbrew – 34C3-Vortrag „Switch Security“](https://switchbrew.github.io/34c3-slides/)
- [SwitchTools – Zusammenfassung Switch-2-Software (X, unbestätigt)](https://x.com/SwitchTools/status/1937118212933439514)
