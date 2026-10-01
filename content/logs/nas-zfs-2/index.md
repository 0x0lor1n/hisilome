+++
title = "Custom NAS #2: Hardware list"
date = 2026-09-29
description = "Every part of the NAS with the price and where it came from, the pool layout, what is left free on the board, and how long a resilver takes on 6 TB drives."

[taxonomies]
tags = ["nas", "zfs", "hardware", "homelab", "worklog"]

[extra]
series = "nas-zfs"
part = 2
+++
## The build

| # | Part | Model | Price | Where |
|---|------|-------|-------|-------|
| 1 | Motherboard | MSI B250M PRO-VD (mATX; 1x PCIe 3.0 x16, 2x PCIe x1, 1x M.2, 6x SATA, 2x DDR4) | CHF 57.19 | AliExpress |
| 2 | CPU | Intel Core i5-6600T (35 W) | CHF 32.59 | AliExpress |
| 3 | CPU cooler | Xilence I250PWM (70 mm) | CHF 12.70 | Galaxus.ch |
| 4 | RAM | Corsair Vengeance 2x16 GB DDR4-2666 CL16 | CHF 30 | Ricardo.ch, about a year ago |
| 5 | NVMe boot #1 | Samsung 256 GB 2230 (with adapter) | $66.80 | AliExpress |
| 6 | NVMe boot #2 | 256 GB | — | had it, from a 2017 laptop (penrose) |
| 7 | Boot adapter | PCIe x1 → 2x M.2 (ASM1182e, LT0534) | CHF 10.09 | AliExpress |
| 8 | NVMe data | 2x 1 TB | — | had them |
| 9 | NVMe switch | PCIe x16 → 4x M.2 (ASM2824 "Split-Free", Gen3 x8) | ~CHF 73 | AliExpress |
| 10 | HDD `tank` | 3x Seagate IronWolf 6 TB (CMR) | 3x ~CHF 201 | AliExpress |
| 11 | HDD `backup` #1 | Seagate Barracuda 6 TB (ST6000DM003, SMR) | — | had it, pulled from an external Porsche Design |
| 12 | HDD `backup` #2 | Seagate Barracuda 6 TB (ST6000DM003, SMR) | CHF 139.12 | Amazon, about a year ago |
| 13 | 10G network | M.2 → SFP+ (Intel JL82599EN, "X520-DA1"), needs SATA power | CHF 31.39 | AliExpress |
| 14 | SFP+ cable | 3 m | $13.52 | AliExpress |
| 15 | PSU | be quiet! Pure Power 12 M 550 W (80+ Gold, ATX 3.0, 5x SATA + 2x Molex, 160 mm) | CHF 68.45 | Galaxus.ch, used |
| 16 | Power adapter | Molex → SATA (for the M.2 → SFP+ card; the PSU has no 6th SATA plug) | — | had it |
| 17 | SATA data cables | 5 pcs (3 IronWolf + 2 Barracuda) | CHF 6.80 | AliExpress |
| 18 | 3x 3.5" cage | Steel three-storey cage, sits on the floor of the main chamber; holds the 2x Barracuda `backup` (one storey apart) | CHF 10.59 | AliExpress |
| 19 | Fan splitter | 4-pin 1→2 on SYS_FAN (front 200 mm + rear 120 mm) | ~CHF 2 | AliExpress |
| 20 | Case | Thermaltake Divider 200 TG (mATX, 3x 3.5" + 3x 2.5") | CHF 75 | Ricardo.ch |
| 21 | Video adapter | VGA → HDMI | CHF 7.60 | Amazon |

**Total:** ≈ CHF 1 223 + $80 ≈ **CHF 1 290**, not counting the "had it" rows; prices with ~ are estimates.

## Layout

| Pool | Drives | Role |
|------|--------|------|
| `rpool` | 2x NVMe 256 GB, mirror (PCIe x1 → ASM1182e) | OS |
| `fast` | 2x NVMe 1 TB, mirror (ASM2824, slots 1–2) | hot data, attic, docker, VMs |
| `tank` | 3x IronWolf 6 TB, raidz1, ~11 TiB usable | main storage |
| `backup` | 2x Barracuda SMR 6 TB, two separate 6 TB pools | warm backup of `tank` |

SMR stays out of RAID. A backup target is the right job for them: `zfs send | recv` writes sequentially, there is no resilver. Two separate pools instead of a stripe, so the death of the older Barracuda does not take the second one down. On the backup: `recordsize=1M`, `compression=zstd`, fill ≤ 80 %. Nightly on a timer: `zpool import` → `zfs send -I` → `zpool export`; between runs the drives sleep and the pool is invisible to the host. Retention on the backup is never longer than on `tank`; media that can be downloaded again is not backed up.

Occupancy: PCIe x16 1/1, PCIe x1 1/2, M.2 1/1, SATA 5/6, DIMM 2/2, 3.5" bays 5/6, NVMe on the ASM2824 2/4.

## Failure model and tiers

raidz1 survives one drive. A second drive dying during resilver is the main argument against raidz1 on six disks; the warm backup here is a compensating control, not a "just in case".

| Event | What saves you | What you lose |
|---|---|---|
| 1 drive in `tank` | resilver | nothing, pool degraded but alive |
| 2nd drive during resilver | warm backup | data since the last `zfs send` |
| drive in warm backup | `tank` | nothing, send it again |
| everything at once (PSU, lightning, ransomware, fire) | cold backup | up to the cold RPO |

**Warm** is a copy, not a source, so no parity: a dead backup drive means another `zfs send` (~30 TB at 10 Gbit ≈ 8 h), not a loss. A stripe of unequal drives is acceptable for warm: any drive dies, the whole copy dies, and that is a fine scenario for a copy.

Procedures:

- `zfs send -I` daily on a timer → warm RPO = one day.
- Drive dies in `tank` → first a final `zfs send` to warm (pool degraded but readable), then `zpool replace`. We enter the resilver window with RPO = 0. No replication during resilver.
- `zpool scrub` of the warm pools monthly: a stripe has no redundancy, scrub repairs nothing, but it shows bad blocks while `tank` is alive and the dataset can be sent again.
- Restore at least one dataset back once, so the path is proven. A full 30 TB restore from an SMR stripe ≈ 20–30 h, the NAS is out of service meanwhile.

**Cold** is partial for now: documents, KeePass databases and 2FA exports on a Kingston IronKey; the photo archive on an external HDD. A cold copy of the whole array and ECC memory are the next NAS build, not this one. Cold covers power, ransomware and operator error only if it lives outside the NAS; fire and theft only if it lives in another building.

**Vector:** `tank` → 6x 6 TB CMR raidz1 (30 TB), warm → 18 TB CMR + 2x 6 TB SMR (30 TB) in an external box over PCIe x1. Split: attic, VMs, documents, photos (many small increments) on the 18 TB CMR; the media library (large sequential files) on the SMR. No headroom on the backup side, so `tank` stays under 80 % (~22 TiB) with ~5 TiB for snapshot history. Later the SMR pair gets replaced by a second 18 TB → 36 TB.

## Room to grow

- **1x SATA** on the board: a 4th IronWolf in `tank` via raidz expansion (ZFS ≥ 2.3, ~16 TiB; old data keeps the old parity layout until rewritten), or one more backup drive.
- **2x M.2** on the ASM2824: `fast` grows when it fills up.
- **1x PCIe x1**: ASM1166 (6x SATA, supports port multipliers) + an eSATA bracket → an external box for the warm backup (18 TB + 2x 6 TB SMR, own power). Box off → cold; box on and `zpool import` → warm.

## Appendix A: rebuild time after a drive swap

Ranges from Synology and TrueNAS forum reports plus arithmetic on average HDD throughput (~140 MB/s for 6 TB CMR). Conditions: idle array, CMR drives, raidz1 ~70 % full.

| Array | RAID5 (mdadm, Synology) | SHR-1 | raidz1 (ZFS) |
|---|---|---|---|
| 6x 6 TB | 10–16 h | 10–18 h | 5–9 h |
| 6x 10 TB | 16–28 h | 18–30 h | 9–15 h |
| 6x 16 TB | 24–40 h | 26–45 h | 14–24 h |

Legend:

- SMR drives → ×3–5.
- Array under load during rebuild → ×1.5.
- RAID5/SHR read the whole disk, time does not depend on fill. raidz1 resilvers only allocated blocks: an empty pool takes minutes, a full one is RAID5.
- DSM throttles rebuild speed by default ("Balanced"/"Low impact"); in "Low impact" 6 TB stretches to 2–3 days.
- A read error on a surviving drive mid-rebuild: mdadm kicks the drive and the array collapses; ZFS marks one file as damaged and carries on.

Our `tank` (3x 6 TB, ~70 %): ~4 TB of data per drive, resilver 6–8 h.

Sources:

- https://sraidcalculator.com/blog/synology-nas-rebuild-time
- https://community.synology.com/enu/forum/1/post/140325
- https://forums.truenas.com/t/long-resilver-time-tl-dr/29218
- https://www.truenas.com/community/threads/drive-size-and-resilvering-times.95917
- https://louwrentius.com/zfs-resilver-performance-of-various-raid-schemas.html

## Appendix B: power draw and running cost

Estimate from component datasheets. Wall figures assume ~87 % PSU efficiency at 10–20 % load (80+ Gold). Measured figures with a wall meter: separate worklog after the build.

| Component | Idle | Load |
|---|---|---|
| i5-6600T + B250M + 2x DDR4 | 14 W | 45 W |
| 3x IronWolf 6 TB (`tank`, spinning / standby) | 12 W / 2.5 W | 16 W |
| 2x Barracuda 6 TB (`backup`, standby, pool exported) | 0.5 W | 11 W (during `zfs recv`) |
| 4x NVMe | 2.5 W | 8 W |
| ASM2824 switch | 5 W | 6 W |
| ASM1182e adapter | 1.5 W | 1.5 W |
| X520-DA1 + DAC | 6 W | 6 W |
| Fans (200 + 120 + CPU) | 3 W | 4 W |
| **DC total** | **~45 W** (`tank` standby: ~36 W) | **~98 W** |
| **At the wall** | **~52 W** (`tank` standby: ~41 W) | **~113 W** |

Load = scrub or nightly `zfs send`; runs a few hours a day at most. `tank` spins down after inactivity (planned, timeout to be tuned against spin-up count in SMART).

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

Meter fee (CHF 7.24/month) is fixed per household and not attributed to the NAS. Vitale Vert 100 % would be 30.9 ct/kWh.

| Scenario | Average draw | kWh/year | CHF/year | CHF/month |
|---|---|---|---|---|
| Idle 24/7, `tank` spinning | 52 W | 456 | 124 | 10.3 |
| Idle 24/7, `tank` standby | 41 W | 359 | 97 | 8.1 |
| 14 h standby + 8 h spinning + 2 h load | 51 W | 447 | 121 | 10.1 |
| Load 24/7 (upper bound) | 113 W | 990 | 268 | 22.4 |

Largest single consumers at idle with `tank` in standby: X520 (6 W, ~15 %), ASM2824 (5 W), CPU + board (14 W). Spin-down of `tank` is worth ~11 W at the wall / CHF 24–27 per year.

Reference: DS923+ with 4 drives, ~40 W active / ~17 W with HDD hibernation → ~250–350 kWh/year → CHF 68–95 at the same tariff.

Source: https://media.sig-ge.ch/documents/tarifs_reglements/electricite/tarifs/tarifs_electricite_tous_clients.pdf

## Appendix C: deferred to the next build

Decided, not implemented here. Each one either needs different hardware or does not pay off at this size.

| Feature | What it solves | Why not now | What it takes |
|---|---|---|---|
| ECC RAM | Bit flips in RAM before ZFS checksums the block; ZFS cannot detect these | B250M / i5-6600T do not support ECC | W680 or C246 board + Xeon E / i3 with ECC, or AM4/AM5 board with ECC UDIMM validated (ASRock Rack); ECC UDIMM |
| ZFS `special` vdev on its own NVMe mirror | Metadata and small blocks on SSD: directory listings, `find`, rsync scans, small-file datasets stop touching HDD | Media-heavy pool at 30 TB, ARC 32 GB covers hot metadata; losing `special` loses the pool, so it must be a mirror, and both spare M.2 slots on the ASM2824 are reserved for growing `fast` | 2x NVMe (~1 % of pool size, 256–512 GB) on a dedicated mirror; `special_small_blocks` per dataset |
| Hot plugging | Swap a failed drive without powering down; no resilver interruption from a reboot | Divider 200 has fixed cages, no backplane; drives are cabled directly | Case with hot-swap bays and SATA backplane (or a 5-in-3 cage), AHCI hot-plug enabled in BIOS, `zpool replace` by `/dev/disk/by-id` |
| Cold backup of `tank` | Full offline copy in another building: fire, theft, ransomware, operator error | Partial cold only: KeePass DBs + 2FA export on Kingston IronKey, photo archive on an external HDD | 2x 18 TB or a second NAS at another site; rotate monthly; `zfs send` to it, then export and unplug |
| UPS | Clean shutdown on power loss; no interrupted resilver or scrub; HDD heads park under power, not on a crash | ZFS itself survives a power cut (transactional, copy-on-write); the remaining risk is mechanical and a mid-resilver cut on raidz1 | 600–900 VA line-interactive (APC Back-UPS, Eaton Ellipse), USB, NUT on NixOS with `services.ups`; ~CHF 150–250 |
| L2ARC | Second-level read cache on NVMe when the working set does not fit in ARC | ARC 32 GB is not saturated by a media workload; L2ARC only helps once ARC hit rate drops; L2ARC headers consume ARC | One NVMe (no mirror needed, loss is harmless), `zpool add tank cache`, persistent since ZFS 2.0; add after seeing `arcstat` hit rate < 90 % |

