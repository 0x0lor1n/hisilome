+++
title = "Custom NAS #2: Hardware list"
date = 2026-09-29
description = "Every part of the NAS with the price and where it came from, the pool layout, failure model, how long a resilver takes on 6 TB drives, and what it costs to run."

[taxonomies]
tags = ["nas", "zfs", "hardware", "homelab", "worklog"]

[extra]
series = "nas-zfs"
part = 2
+++
## The build

### Core

| # | Part | Model | Price CHF | Where | Condition | Bought | Installed |
|---|------|-------|-------|-------|-----------|--------|-----------|
| 1 | Motherboard | [MSI B250M PRO-VD](https://www.msi.com/Motherboard/b250m-pro-vd/Specification) | 57.19 | AliExpress | refurbished | 29.12.2024 | 28.04.2025 |
| 2 | CPU | [Intel Core i5-6600T](https://www.intel.com/content/www/us/en/products/sku/88189/intel-core-i56600t-processor-6m-cache-up-to-3-50-ghz/specifications.html) | 32.59 | AliExpress | refurbished | 02.03.2025 | 28.04.2025 |
| 3 | CPU cooler | [Xilence I250PWM](https://www.galaxus.ch/en/s1/product/xilence-i250pwm-70-mm-cpu-coolers-10144489) | 12.70 | Galaxus.ch | new | 13.03.2025 | 28.04.2025 |
| 4 | RAM | [Corsair CMK32GX4M2A2666C16R](https://www.corsair.com/ch/en/p/memory/cmk32gx4m2a2666c16r/vengeancea-lpx-32gb-2-x-16gb-ddr4-dram-2666mhz-c16-memory-kit-red-cmk32gx4m2a2666c16r) | 30 | Ricardo.ch | new | 27.03.2025 | 28.04.2025 |
| 5 | PCIe x16 | [ASM2824 (PCIe x16 → 4x M.2)](https://de.aliexpress.com/item/1005012647619070.html) | 74.52 | AliExpress | new | 27.09.2026 | 12.10.2026 |
| 6 | M.2 | [Intel JL82599EN (M.2 → SFP+)](https://de.aliexpress.com/item/1005008046633237.html) | 31.39 | AliExpress | new | 26.09.2026 | - |
| 7 | PSU | [be quiet! Pure Power 12 M 550 W](https://www.galaxus.ch/en/s1/product/be-quiet-pure-power-12-m-550-w-power-supply-pc-24077999) | 68.45 | Galaxus.ch | used | 08.10.2026 | 13.10.2026 |
| 8 | Case | [Thermaltake Divider 200 TG Air](https://www.digitec.ch/en/s1/product/thermaltake-divider-200-tg-air-black-matx-pc-case-16805400) | 65 | Ricardo.ch | new | 01.03.2025 | 28.04.2025 |

**Total: CHF 372**

### Utilities

| # | Part | Model | Price CHF | Where |
|---|------|-------|-------|-------|
| U1 | Cable | [SFP+ DAC Cable, 3 m](https://de.aliexpress.com/item/1005006373736990.html) | 11.23 | AliExpress |
| U2 | Adapter | Molex → SATA | - | had it |
| U3 | Cable | [SATA, 5 pcs](https://de.aliexpress.com/item/1005002966974651.html) | 6.80 | AliExpress |
| U4 | Mount | [Steel three-storey cage for 3.5" SATA](https://de.aliexpress.com/item/1005006907353405.html) | 10.59 | AliExpress |
| U5 | Splitter | [4-pin 1→2 on SYS_FAN](https://de.aliexpress.com/item/1005005845263526.html) | 1.70 | AliExpress |
| U6 | Mount | [50x M3x5 / 6-32 flat-head screws](https://de.aliexpress.com/item/4000798144249.html) | 2.75 | AliExpress |
| U7 | Pads | [Self-adhesive silicone pads, 10x2 mm, 50 pcs](https://de.aliexpress.com/item/1005005315398342.html) | 1.49 | AliExpress |
| U8 | Cable ties | [Self-locking nylon cable ties](https://de.aliexpress.com/item/1005007615502103.html) | 1.54 | AliExpress |

**Total: CHF 36**

### Data drives

| # | Part | Model | Price CHF | Where | Condition | Bought | Installed |
|---|------|-------|-------|-------|-----------|--------|-----------|
| S1 | NVMe `rpool` | [Samsung PM9B1 2230 256 GB](https://de.aliexpress.com/item/1005012443075835.html) | 55.51 | AliExpress | new | 03.03.2025 | 10.10.2026 |
| S2 | NVMe `fast` #1 | [Samsung PM9A1 1 TB](https://www.techpowerup.com/ssd-specs/samsung-pm9a1-1-tb.d786) | - | had it | used | - | 12.10.2026 |
| S3 | NVMe `fast` #2 | [Samsung PM981a 1 TB](https://www.techpowerup.com/ssd-specs/samsung-pm981a-1-tb.d782) | - | had it | used | - | 12.10.2026 |
| S4 | HDD `tank` #1 | Seagate IronWolf Pro 6 TB | 200.99 | AliExpress | new | 26.09.2026 | 12.10.2026 |
| S5 | HDD `tank` #2–3 | [2x Seagate IronWolf Pro 6 TB](https://de.aliexpress.com/item/1005012574414150.html) | 2x 202.39 | AliExpress | new | 30.09.2026 | 12.10.2026 |
| S6 | HDD `backup` #1 | Seagate Barracuda 6 TB | - | had it | used | - | - |
| S7 | HDD `backup` #2 | [Seagate Barracuda 6 TB](https://www.amazon.fr/dp/B07H28SY39) | 139.12 | Amazon.fr | new | 24.03.2025 | - |

**Total: CHF 800**

**Build total: CHF 1 208**

## Not in the build

### Debugging gear

Bought for bring-up and troubleshooting; not part of the final build.

| # | Part | Model | Price CHF | Where |
|---|------|-------|-------|-------|
| D1 | USB expansion card | [4-port USB 3.0 PCIe](https://de.aliexpress.com/item/4000883555797.html) | 6.87 | AliExpress |
| D2 | Keyboard adapter | [PS/2 male → USB-A female](https://de.aliexpress.com/item/1005005617742005.html) | 2.36 | AliExpress |
| D3 | Front-panel adapter | [USB 2.0 9-pin → USB-C (Type-E)](https://de.aliexpress.com/item/1005008299025239.html) | 2.48 | AliExpress |
| D4 | Video adapter | [VGA → HDMI](https://www.amazon.fr/dp/B09T2HQRTL) | 7.60 | Amazon.fr |
| D5 | M.2 adapter | [ASM1182e (PCIe x1 → 2x M.2)](https://de.aliexpress.com/item/1005008742918331.html) | 10.09 | AliExpress |
| D6 | Input device | Arduino Pro Micro (PS/2 / USB) | - | had it |

**Total: CHF 29**

### Failures

Parts that died in service and were replaced.

| # | Part | Model | Price CHF | Where | Condition | Bought | Installed | Replaced | Cause |
|---|------|-------|-------|-------|-----------|--------|-----------|----------|-------|
| F1 | PSU | [LC-Power LC420-12](https://www.galaxus.ch/en/s1/product/lc-power-lc420-12-350-w-power-supply-pc-5684873) | 31.90 | Galaxus.ch | new | 13.03.2025 | 28.04.2025 | 13.10.2026 | A short circuit made it unstable |

**Total: CHF 31.90**

## SMART

Snapshots taken with `smartctl -x`, one row per drive and reading.

### NVMe

| # | Date | Power-on h | Power cycles | Unsafe shutdowns | Written | Used | Media errors |
|---|------|------------|--------------|------------------|---------|------|--------------|
| S1 | 12.10.2026 | 16 | 136 | 56 | 1.34 TB | 0 % | 0 |
| S2 | 12.10.2026 | 3 426 | 101 | 26 | 6.07 TB | 9 % | 161 |
| S3 | 12.10.2026 | 2 983 | 73 | 15 | 7.22 TB | 1 % | 0 |

### HDD

| # | Date | Power-on h | Start/stop | Load cycles | Reallocated | Pending | Uncorrectable | CRC errors | Max temp |
|---|------|------------|------------|-------------|-------------|---------|---------------|------------|----------|
| S4 | 12.10.2026 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 27 °C |
| S5a | 12.10.2026 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 26 °C |
| S5b | 12.10.2026 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 29 °C |
| S6 | 12.10.2026 | 28 197 | 4 646 | 13 452 | 0 | 0 | 2 | 0 | 58 °C |
| S7 | 12.10.2026 | 5 | 64 | 65 | 0 | 0 | 0 | 0 | 35 °C |

> **Note:** everything below describes the final configuration, not the current one: the ASM2824 carries the OS NVMe and 3x 1 TB for `fast`; `tank` as 6x 6 TB IronWolf Pro raidz1 on the onboard SATA ports; both PCIe x1 slots are left for SATA controllers (up to 8 more drives without a bandwidth penalty), one of them drives the warm backup (18 TB + 2x 6 TB) in an external box with its own power supply; a NanoKVM-PCIe with PoE sits in the fifth case slot.

## Layout

| Pool | Drives | Role |
|------|--------|------|
| `rpool` | 1x NVMe 256 GB (ASM2824), no mirror | OS |
| `fast` | 3x NVMe 1 TB, raidz1 (ASM2824), ~1.8 TiB usable | Jellyfin, TorrServer, Nix cache, etc. |
| `tank` | 6x IronWolf Pro 6 TB, raidz1, ~27 TiB usable | main storage |
| `backup` | 1x 18 TB CMR + 2x Barracuda SMR 6 TB, stripe, ~27 TiB usable (external box) | warm backup of `tank` |

`rpool` is not mirrored: if the OS drive dies, the NanoKVM gives remote access to the BIOS, and the box netboots over PXE from the router until the drive is replaced. `fast` starts as a mirror of the two existing 1 TB drives and becomes raidz1 once the third arrives.

## Failure model and tiers

| Event | What saves you | What you lose |
|---|---|---|
| 1 drive in `tank` | resilver | nothing, pool degraded but alive |
| 2nd drive during resilver | warm backup | data since the last `zfs send` |
| drive in warm backup | `tank` | nothing, send it again |
| everything at once (PSU, lightning, ransomware, fire) | nothing | everything outside the partial cold copy |

**Cold**, partial: documents, KeePass databases and 2FA exports on a Kingston IronKey; photo archive on an external HDD.

## Appendix A: rebuild time after a drive swap

Ranges from Synology and TrueNAS forum reports plus arithmetic on average HDD throughput (~140 MB/s for 6 TB CMR). Conditions: idle array, CMR drives, raidz1 ~70 % full.

| Array | RAID5 (mdadm, Synology) | SHR-1 | raidz1 (ZFS) |
|---|---|---|---|
| 6x 6 TB | 10–16 h | 10–18 h | 5–9 h |
| 6x 10 TB | 16–28 h | 18–30 h | 9–15 h |
| 6x 16 TB | 24–40 h | 26–45 h | 14–24 h |

<small><em>(Multiply times: ×3–5 for SMR drives, ×1.5 if the array is under load during rebuild.)</em></small>

Legend:

- RAID5/SHR read the whole disk, time does not depend on fill. raidz1 resilvers only allocated blocks: an empty pool takes minutes, a full one is RAID5.
- DSM throttles rebuild speed by default ("Balanced"/"Low impact"); in "Low impact" 6 TB stretches to 2–3 days.
- A read error on a surviving drive mid-rebuild: mdadm kicks the drive and the array collapses; ZFS marks one file as damaged and carries on.

Our `tank` (6x 6 TB, ~70 %): ~4 TB of data per drive, resilver 5–7 h.

Sources:

- https://sraidcalculator.com/blog/synology-nas-rebuild-time
- https://community.synology.com/enu/forum/1/post/140325
- https://forums.truenas.com/t/long-resilver-time-tl-dr/29218
- https://www.truenas.com/community/threads/drive-size-and-resilvering-times.95917
- https://louwrentius.com/zfs-resilver-performance-of-various-raid-schemas.html

## Appendix B: power draw and running cost

Estimate from component datasheets. Wall figures assume ~87 % PSU efficiency at 10–20 % load (80+ Gold).

| Component | Idle | Load |
|---|---|---|
| i5-6600T + B250M + 2x DDR4 | 14 W | 45 W |
| 6x IronWolf Pro 6 TB (`tank`, spinning / standby) | 42 W / 6 W | 49 W |
| 4x NVMe | 2.5 W | 8 W |
| ASM2824 switch | 5 W | 6 W |
| ASM1166 (PCIe x1 → eSATA, warm box) | 2 W | 2 W |
| 82599EN + DAC | 6 W | 6 W |
| Fans (200 + 120 + CPU) | 3 W | 4 W |
| **DC total** | **~75 W** (`tank` standby: ~39 W) | **~120 W** |
| **At the wall** | **~86 W** (`tank` standby: ~44 W) | **~138 W** |
| Warm box, own PSU (18 TB + 2x 6 TB), at the wall | ~2 W (standby, pool exported) | ~25 W (during `zfs recv`) |

<small><em>(Measured figures with a wall meter: separate worklog after the build.)</em></small>

Load = scrub or nightly `zfs send`; runs a few hours a day at most. Scenarios include the warm box: standby except 2 h of nightly send, ~4 W average. `tank` spins down after inactivity (planned, timeout to be tuned against spin-up count in SMART).

SIG tariff 2026, Profil Simple, Électricité Vitale Vert 10 % (reference product), VAT included:

| Item | ct/kWh |
|---|---|
| Energy | 11.24 |
| Grid use | 11.35 |
| Cantonal levy (13.2 % of grid use) | 1.50 |
| Federal renewable surcharge | 2.49 |
| Federal electricity reserve | 0.44 |
| Solidarity costs | 0.05 |
| **Total** | **27.1** |

Meter fee (CHF 7.24/month) is fixed per household and not attributed to the NAS.

| Scenario | Average draw | kWh/year | CHF/year | CHF/month |
|---|---|---|---|---|
| Idle 24/7, `tank` spinning | 90 W | 788 | 214 | 17.8 |
| Idle 24/7, `tank` standby | 48 W | 420 | 114 | 9.5 |
| 14 h standby + 8 h spinning + 2 h load | 70 W | 613 | 166 | 13.8 |
| Load 24/7 (upper bound) | 163 W | 1428 | 387 | 32.2 |

Source: https://media.sig-ge.ch/documents/tarifs_reglements/electricite/tarifs/tarifs_electricite_tous_clients.pdf

## Appendix C: deferred to the next build

Each needs different hardware or does not pay off at this size.

| Feature | What it solves | Why not now | What it takes |
|---|---|---|---|
| ECC RAM | Bit flips in RAM before ZFS checksums the block; ZFS cannot detect these | B250M / i5-6600T do not support ECC | W680 or C246 board + Xeon E / i3 with ECC, or AM4/AM5 board with ECC UDIMM validated (ASRock Rack); ECC UDIMM |
| ZFS `special` vdev on its own NVMe mirror | Metadata and small blocks on SSD: directory listings, `find`, rsync scans, small-file datasets stop touching HDD | Media-heavy pool at 30 TB, ARC 32 GB covers hot metadata; losing `special` loses the pool, so it must be a mirror, and all four M.2 slots on the ASM2824 are taken by `rpool` and `fast` | 2x NVMe (~1 % of pool size, 256–512 GB) on a dedicated mirror; `special_small_blocks` per dataset |
| Hot plugging | Swap a failed drive without powering down; no resilver interruption from a reboot | Divider 200 has fixed cages, no backplane; drives are cabled directly | Case with hot-swap bays and SATA backplane (or a 5-in-3 cage), AHCI hot-plug enabled in BIOS, `zpool replace` by `/dev/disk/by-id` |
| Cold backup of `tank` | Full offline copy in another building: fire, theft, ransomware, operator error | Partial cold only: KeePass DBs + 2FA export on Kingston IronKey, photo archive on an external HDD | 2x 18 TB or a second NAS at another site; rotate monthly; `zfs send` to it, then export and unplug |
| UPS | Clean shutdown on power loss; no interrupted resilver or scrub; HDD heads park under power, not on a crash | ZFS itself survives a power cut (transactional, copy-on-write); the remaining risk is mechanical and a mid-resilver cut on raidz1 | 600–900 VA line-interactive (APC Back-UPS, Eaton Ellipse), USB, NUT on NixOS with `services.ups`; ~CHF 150–250 |
| L2ARC | Second-level read cache on NVMe when the working set does not fit in ARC | ARC 32 GB is not saturated by a media workload; L2ARC only helps once ARC hit rate drops; L2ARC headers consume ARC | One NVMe (no mirror needed, loss is harmless), `zpool add tank cache`, persistent since ZFS 2.0; add after seeing `arcstat` hit rate < 90 % |

