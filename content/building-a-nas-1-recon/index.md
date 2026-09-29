+++
title = "Building a NAS #1: Recon and Decision Making"
date = 2026-09-29
description = "Why not Synology, why ZFS, what goes on which disks, and how an old MSI B250M board ends up with 10 Gbit, an NVMe cluster and a mirrored OS on a PCIe x1 slot."

[taxonomies]
tags = ["nas", "zfs", "nixos", "hardware", "homelab"]

[extra]
series = "building-a-nas"
part = 1
+++
For past ~20 years I have collected data of different type. Not so much though (~4 TB). Four years ago I started doing outdoor activities and got a GoPro. The thing is very video hungry and I am dumping it too slow.

My storage was growing up too: USB sticks, external drives, HDDs, SSDs, sometimes even a very old computer. So I have bought this 6 TB Porsche Design drive. That was a newbie mistake: two years later it stopped responding and system (Linux) was not detecting it anymore and it was a nightmare to fix.

Disclaimer: why I don't use cloud storage: clouds lost my trust long time ago. Personal experience: Meta (whatsapp + facebook) was posting pictures from *my* archives to their platforms without my approval. This is against my rules what goes online. Another example: some friends had an issue with Apple's cloud - pictures they deleted were showing up in albums after 5 years.

{% dialogue() %}
KRITON. So the cloud posted your photos.

0x0lor1n. Without asking.

KRITON. And your fix is a box in your apartment.

0x0lor1n. A box I can open.

KRITON. You called the last one a newbie mistake.

0x0lor1n. I opened that one too.
{% end %}

When it stopped being recognized I tried to open the case, calmly. Took me like an hour and a half, bent two steel pry bars and cut a finger. Then I looked in the web for a guy who by Murphy's law solved this problem. Found one, a guy who filmed the process of opening similar Porsche Design case. Turns out: there is a latch invisible from outside you need to slide out.

So after that I made diagnostics of the hard drive and happily got as result: only the control board is dead, the information on it safe. Ordered a new shell/controller assembly set from AliExpress - problem solved.

Since that moment I wanted a better solution. A year ago I became tired of my other projects and remembered about this open issue. At that time I already obtained some experience in self hosting, hardware development and most importantly - fixing things that were broken by me.

## Recon

Any project starts with "1. Recon" in notebook. I started the old school way: looking for engineers that I know at work/telegram/past, trying to find videos on youtube, reading top-N lists in search results. Most of the people were using Synology; in top-N lists there was only one alternative - QNAP; on YouTube I found couple TrueNAS reviews and tons of enterprise solutions review videos on Supermicro motherboards.

I was checking Synology first and quickly realized it was not my cup of tea for two reasons: closed source software; main feature: proprietary type of RAID (read about it, could not find anything different from regular RAID 5). QNAP - same story. If I self host, I can just spend couple evenings setting up software myself and with that logic I started to read how TrueNAS is constructed and what enterprise offers.

For the sake of the reseatch I checked what Synology offers for my build budget (~1300CHF). The nearest in terms of drive bays is DS1525+. At that price you get one item out of three: 10 Gbit, or more drives, or NVMe. And they allow to use *only* their own NVMe drives in a pool at the price of 350CHF per 800 GB. Everything together (SFP+, an NVMe pool and a second pool for backup) is twice as expensive. The only advantage Synology has at the same price - ECC memory. I don't count DSM out of the box as advantage (two pals set up their DS923+ in one evening and never thought about it again).

## File system

The first topic in this agenda was the classic mdadm setup for RAID arrays. Quick PoC (two days of work) and I had RAID 10 on btrfs in QEMU virtual machine running. Forums + investigation led to discovery of ZFS (I have heard about it couple times in the basements of system administrators). Ran similar test with RAIDZ1 and knew: this is it.

First thing: ZFS solves power loss during a write - it just rolls back on restart to the state after last completed copy-on-write operation. Transaction in flight at the moment of shutdown is lost, obviously. Benchmarks in QEMU: only last 1–5 seconds before shutdown are gone.

It also corrects bit-flips by default. With a notice: only if we have redundancy (mirror/RAIDZ) + regular scrub. No recovery out of thin air, no defragmentation - only deltas in snapshots. Elegant.

Since OpenZFS v2.3 there is RAIDZ expansion on a live RAIDZ: you can add a disk to RAIDZ without rebuilding it. Old data remains in the old parity layout and usable space increases by less than the full disk until the data gets re-written. After that - no reasons not to use ZFS remain. In reality RAIDZ1 ~ RAID 5, RAIDZ2 ~ RAID 6, but with a checksum on every block, self healing, no write hole.

## Operating system

NixOS. Whole system state is declared in git, that makes maintenance and development simple.

## What goes on the disks

Before picking drives I need to understand what data goes to the NAS.

ZFS:

- Everything that is PII: megabytes. Encrypted ZFS dataset. Slow reads are fine.
- Music, old projects, torrent downloads, backups, GoPro video, photos: terabytes. Unencrypted dataset. Slow reads.
- Nix cache for builds (I am a Nix user): gigabytes. Unencrypted dataset. Fast reads.
- Databases, Docker containers, virtual machines: gigabytes. Unencrypted dataset. Fast reads.

btrfs:

- Operating system: gigabytes. No encryption needed. Fast reads.

Why put it on btrfs and not on ZFS too? For simplicity: Btrfs is available out of the box in kernel, mirror - one command; snapshots are there. The OS must be fault tolerant - RAID 1 mirror on btrfs.

*Update from the build.* I reevaluated the meaning of the term "simplicity" so the OS went to ZFS too. All USB ports on the board turned out dead (how - in part 3), so if OS drive dies I can't even plug a stick to reinstall. The OS needs a mirror I trust, and ZFS on root on NixOS turned out to be two datasets and a bootfs. One file system for everything.

## Slow data

So after some benchmarking and drives I had - I decided to go with 6 TB drives. That means RAIDZ1 on three = 12 TB usable space. One of my drives was very active for a while, so it's better to make RAIDZ2 from the beginning. RAIDZ2 on four = 12 TB usable.

I also need place for a warm copy, so one SATA port - drive with many TB. Six SATA ports is a de-facto standard for some class of motherboards. So maximum configuration for an HDD NAS with warm backup on six SATA ports would be 5 × 6 TB SATA HDD in RAIDZ2 (18) + 1 × 18 TB SATA HDD for "warm" backup.

On five SATA ports: 4 × 6 TB SATA HDD in RAIDZ2 + 1 × 12 TB SATA HDD for the backup. On four: 3 × 6 TB in RAIDZ1 + 1 × 12 TB.

*Update from the build.* Well, two of my Barracudas were SMR. Rebuild on shingled drives is a matter of days instead of hours, so no raidz for them. New drives - CMR only: IronWolf, Exos, WD Red Plus. Barracudas became the backup pool: three IronWolf in raidz1, two Barracuda as a plain stripe with zfs send on cron and spin-down when idle. Stripe means no redundancy: one dead Barracuda and the copy is gone. Fine for a copy - the main pool does not even notice it, zfs send rebuilds it overnight. One SATA port left.

## Fast data

NVMe SSD only for quick read of data. No RAID: it's basically a cache and can be lost on crash. Database or VM are the exception. They need mirror on two NVMe drives OR snapshot + zfs send to HDD pool on cron basis. Otherwise dead NVMe drive = lost state. I found two 1 TB NVMe in the closet that together form a nice zfs mirror of 1 TB. It is not clear yet if it's enough (asked a colleague of mine, he said 512 GB – 1 TB would be his choice), so the system should support at least 2 more slots for NVMe.

## No place is like 127.0.0.1

NVMe SSD for the Operating System. NixOS wants to write a lot to /nix/store. A btrfs mirror requires at least two NVMe drives. In the closet I found one 256 GB NVMe drive and one 256 GB M.2 2232 with an M.2 adapter -> that's what's up.

Result: at least 5 SATA ports and 6 or more NVMe slots. Already at this point it was clear I will hardly find a board with 6+ NVMe slots. That was going to be the interesting part.

## The rest of the hardware

- Low power consumption.
- 10Gbit/s network. Reasoning: My home network supports 10GBit/s over SFP+ and RJ45. Actively used Nix cache needs at least 2.5 Gbit link, so if possible - design for 10Gbit/s.
- Well-ventilated case to keep the microclimate healthy.
- No TPM. PII will be encrypted, and in all my projects I use age + TPM encryption from the host for PII and sensitive data. Nothing to encrypt on this machine. That opens the market of old motherboards = noice.

With picture somewhat clear it was time to go deep into home lab corners of internet. The most interesting discussions I found were on 4pda.ru in the NAS configurations thread. After week of comparing motherboard/cpu combos I decided to pick MSI B250M PRO-VD with Intel Core i5-6600T. I have talked to the author of that build on the forum and got an idea how this combo performs in reality. Better than any documentation. Learned couple tricks for stock bios and went for my first NAS build.

The board has 6 SATA ports, 1 M.2 slot, 1 PCIe x16 gen 3, and 2 PCIe x1.

Its chipset supports maximum 2 × 16 GB of RAM, not ECC, but that looked enough for my usage. ECC support is the borderline between professional and hobbyist implementations. By restraining myself to no ECC I have narrowed down list of good low power mothers a lot.

For NVMe cluster + 10 Gbit NIC it is ideal to have two PCIe x16 slots, which was not the case with that mother. I had experience in M.2 - OCuLink conversion, so the idea of using M.2 slot as a second PCIe came quick. Why not put NIC on PCIe x1? PCIe x1 gen 3 provides bandwidth ~985 MB/s. 10 Gbit Ethernet or SFP+ interface requires ~1.25 GB/s. So PCIe x1 is not enough and the NIC goes to M.2 slot through an M.2-to-SFP+ adapter. The chip on that card, an Intel 82599, is PCIe 2.0: on four lanes it's about 2 GB/s which is more than enough.

With M2 being used for 10Gbit/s channel and all the SATA drives reserved for the tank: the solution for the NVMe drives became a challenge. That's what I ended up with:

- Fast data: we take main PCIe x16 and put an NVMe expansion card with an onboard switch on it. I was choosing between ASM2824 and LRNV9547L-4L controllers. Picked ASM2824 for lower power consumption. It will distribute the x8 lanes over 4 NVMe drives, so with a PCIe switch it does not matter if your motherboard supports bifurcation or not. Original idea taken from this setup, though they just used a splitter without bifurcation.

{% dialogue() %}
KRITON. You said the M.2 slot was for the OS.

0x0lor1n. It was.

KRITON. And now the network card sits there.

0x0lor1n. Through an adapter. The slot does not give enough power, so the card
has its own connector for SATA power from the supply. Sec, I need to write that down.

KRITON. So where does the OS go?
{% end %}

- OS resides on PCIe x1. A ~~btrfs~~ zfs mirror of two 256 GB NVMe drives is sitting on top of a PCIe x1 to dual NVMe splitter card (ASM1182e). ASM1182e is a PCIe 2.0 switch, so ~500 MB/s for both drives together, ~250 MB/s each under simultaneous load. More than enough for the OS.

The picture came together:

- 6 SATA ports: RAIDZ1 of 3 × IronWolf 6 TB (12 TB usable) + a separate pool of 2 × Barracuda 6 TB striped for the copy (12 TB, no redundancy). 1 SATA port free.
- PCIe x16 slot: NVMe cluster with an onboard switch. 2 × 1 TB for fast data, 2 slots free.
- PCIe x1 slot: ~~btrfs~~ ZFS mirror of 2 × 256 GB for the OS through a PCIe x1 to 2 × M.2 splitter card.
- M.2 slot: NIC through an M.2-to-SFP+ adapter.

## Summary

Recon - over. I know what I can expect from the build, which component is doing what, the picture on paper is clear. One question remains: are two 1 TB NVMe drives enough for fast data? Everything else - no more doubts.

What the setup gives me after recon:

- Meets all the original requirements.
- Lets me start with a small number of drives and add more over time.
- Leaves room for expansion: 1 SATA port, 2 M.2 slots on the NVMe switch card, and PCIe x1 (for example, for an ASM1166 with 6 more SATA ports), Intel QuickSync can transcode HEVC (hello JellyFin?).

What I accept knowingly:

- No ECC. 32 GB of ARC without error correction. Price of an old low-power board, and the one place where Synology at the same money is honestly ahead.
- PCIe x1 adapter is a single point of failure for the OS. ASM1182e dies - both mirror drives go at once. Mitigation: NixOS config is in git, data pool won't notice a reinstall, system is back in half an hour.
- Backup pool is not a 3-2-1 backup. Same case, same PSU. Protects from drive death and my own mistakes (snapshots), not from fire or a 12 V spike. Real cold backup on a shelf is a separate story.
- RAIDZ1 does not turn into RAIDZ2. Expansion adds a disk, the parity level remains forever. Above I said it's better to plan raidz2 from the start, and I changed my mind: three CMR drives in raidz1 + a full copy on a separate pool. For data survival that's raidz2: two drives can die. For uptime it's not: raidz2 keeps serving even with two dead drives, here a second death in the main pool means restoring from the copy. In exchange the copy protects from my own screw-ups. If I want RAIDZ2 - just recreate the pool through the copy.

Next part - work log: list of all components, purchase prices and where they came from.
