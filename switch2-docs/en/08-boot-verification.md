# Boot and Signature Verification in Detail

> This chapter **explains** how the Switch 2 verifies, at every start, that only Nintendo-signed code runs. It is not a guide to bypassing those checks.
>
> **The source is public reverse-engineering documentation** (mainly the Switchbrew/Switch2brew wiki), not the console itself. None of these checks is visible over USB: as measured in [07](07-usb-observations.md), the console only enumerates after ~6.3 s, once boot is already well advanced. The early stages expose nothing externally.
>
> Much is well documented for the Switch 1 and only partly confirmed for the Switch 2. Legend: 🔎 from RE documentation, ❓ unconfirmed / inferred from Switch 1.

## 1. Core idea: chain of trust

Each stage verifies the **signature** of the next stage before starting it. A signature is a mathematical endorsement: Nintendo signs with a **secret private key**, and the console verifies with the matching **public key**. Only Nintendo holds the private key.

```
BootROM  ──verifies──►  first stage  ──verifies──►  next stage  ──verifies──►  …
 (in chip,              (PSC/MB1,                   (Secure Monitor,
  immutable)             on the UFS)                 kernel, …)
```

The **trust anchor** is the BootROM: hard-wired into the SoC, not updatable, with the hash of the public key it checks against stored in eFuses. So nobody can simply substitute their own public key, because its hash would not be in the fuses.

## 2. What a signature check actually does

Using a boot stage as an example:

1. The stage is a file on the UFS, together with a signature and (usually) encrypted.
2. The previous stage computes a **hash** (a checksum) over the content.
3. It uses the **public key** to check whether the signature matches exactly that hash.
4. Only if it matches is the stage decrypted and executed. Otherwise the **boot aborts** (on the Switch 1 with a panic code).

Important: decryption and signature verification are **two separate things**. Encryption keeps the content secret; the signature ensures authenticity. Both must hold.

## 3. The first stage: BR-BCT

The BootROM first loads the **BCT** (Boot Configuration Table), here called **BR-BCT**. It sits at the very start of the boot LUNs (LUN 0 and LUN 1) of the UFS and tells the BootROM where the next stage is and how it is verified.

Per Switchbrew ("Switch 2: BCT" page, 🔎):

| Region | Content |
|---|---|
| Offset 0x0 | magic value (identification) |
| Signature | **XMSS-SHA2_20_256** |
| Hash over 0x44–0x2000 | SHA-512 over almost the whole structure |
| Hash over 0x1200–0x2000 | separate SHA-512 |
| BrBctHash over 0x170C–0x1AC0 | hash over an encrypted section |

### The most striking difference from the Switch 1

- **Switch 1:** RSA-2048 / RSA-PSS (classical public-key cryptography).
- **Switch 2:** **XMSS**, a **hash-based, quantum-computer-resistant** signature scheme.

XMSS (eXtended Merkle Signature Scheme) is built purely on hash functions. Two properties matter here:

1. **Quantum-safe:** a future quantum computer could break RSA and ECC, but not hash-based schemes by today's understanding. For a device in the field for 10+ years, that is sensible.
2. **Stateful:** XMSS has a limited number of possible signatures (here 2²⁰, about a million). Each private key may sign each "position" only **once**. For firmware, which is signed rarely, that is no problem and is manageable for Nintendo.

That Nintendo makes exactly the lowest, non-updatable stage quantum-safe fits the fact that this stage must last for the device's entire lifetime.

## 4. Further stages: PSC, MB1, MBCT

After the BR-BCT come the early stages. A community summary (❓, unconfirmed) names:

- **MB1, PSC firmware, MBCT:** early boot stages, each **signed and stored redundantly** on the boot LUNs.
- A "stage 2" reportedly contains a random salt, the **ECID** (device-specific chip ID), a binding to the BR-BCT, and an **RSA-3072** signature for stage 1.

This sounds like a **mixed approach**: XMSS for the lowest anchor, classical RSA (3072 here vs. 2048 on Switch 1) for later stages. This is not confirmed.

**PSC (Platform Security Controller):** a dedicated small security processor in the SoC. In newer NVIDIA Tegra designs it handles key management and verification of boot stages. It roughly replaces the Switch 1's TSEC/Falcon. How the PSC itself is verified is not publicly documented (❓).

## 5. Later stages: Secure Monitor, kernel, packages

From here the Switch 2 can only be estimated via Switch 1 documentation (🔎 for Switch 1, ❓ for Switch 2):

- **Package1:** early bootloader part plus Secure Monitor code (runs in TrustZone/EL3).
- **Package2:** the **Horizon kernel** plus the core sysmodules.

On the Switch 1, Package2 is laid out as:

| Region | Content |
|---|---|
| Offset 0x0, 0x100 bytes | **RSA-2048 signature**, PKCS#1 v2.1 **RSASSA-PSS** with SHA-256 |
| then | encrypted header |
| then | encrypted body (AES-CTR, key known only to TrustZone) |

If any of these checks fails, boot aborts. For the Switch 1, Switchbrew lists separate panic codes for Package2 signature, meta, version and payload failures (🔎).

## 6. Anti-downgrade via fuses

In addition to signature checks there is **version protection**:

- The eFuses hold a **minimum firmware version** (anti-rollback counter).
- On important updates the console burns another fuse, raising the minimum version.
- Older firmware is **correctly signed**, but its version is below the fuse counter, so boot refuses it anyway.
- Burned fuses cannot be physically reset. A downgrade to an older, possibly vulnerable version is thus permanently blocked.

For the Switch 2 this principle is very likely (❓); the exact fuse assignments are partly listed on the Switchbrew "Switch 2: Fuses" page (🔎). The first 80 fuse words there are stored as 40 **redundant pairs**, which makes glitching attacks on individual fuse bits harder.

## 7. Why this cannot be "sniffed" from outside

- The checks run **inside the SoC**, in the BootROM, PSC and TrustZone. None of it is emitted over USB, the display or any other open channel.
- Keys live in dedicated hardware and never in plaintext in RAM that normal code can access.
- So the only serious source of information is the **RE community's analysis of publicly extracted firmware**. Their results are in the wiki, and this chapter summarizes them.

## 8. Relation to our firmware version

The console in this project still runs the **shipping firmware** (no updates). For boot verification that means:

- The anti-downgrade counter is at its lowest value, so no additional fuses for newer versions have been burned yet.
- The chain described (BR-BCT with XMSS → later stages → Secure Monitor → kernel) is the same. The signature scheme does not change with updates, only the signed contents and the minimum-version counter.

## Sources

- [Switchbrew – Switch 2: BCT](https://switchbrew.org/wiki/Switch_2:_BCT)
- [Switchbrew – BCT (Switch 1)](https://switchbrew.org/wiki/BCT)
- [Switchbrew – Package2](https://switchbrew.org/wiki/Package2)
- [Switchbrew – Package1](http://www.switchbrew.org/wiki/Package1)
- [Switchbrew – Panic codes](https://switchbrew.org/w/index.php?title=Panic_codes&mobileaction=toggle_view_desktop)
- [Switchbrew – Switch 2: Fuses](https://switchbrew.org/wiki/Switch_2:_Fuses)
- [Switchbrew – 34C3 talk "Switch Security"](https://switchbrew.github.io/34c3-slides/)
- [SwitchTools – Switch 2 software summary (X, unconfirmed)](https://x.com/SwitchTools/status/1937118212933439514)
