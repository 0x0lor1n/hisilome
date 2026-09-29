+++
title = "Building a NAS #2: Hardware list"
date = 2026-09-29
description = "Every part of the NAS with the price and where it came from, the pool layout, what is left free on the board, and how long a resilver takes on 6 TB drives."

[taxonomies]
tags = ["nas", "zfs", "hardware", "homelab", "worklog"]

[extra]
series = "building-a-nas"
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

## Appendix: rebuild time after a drive swap

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
