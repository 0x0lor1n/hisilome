+++
title = "penrose: coreboot on a Dell Precision 3520 (Xeon board)"
date = 2026-11-01
description = "Worklog for the laptop: the Xeon board swap, what it took to get coreboot on it, and the numbers — eleven benchmark runs, an undervolt sweep, and the EC fan curve measured and rewritten."
draft = true

[taxonomies]
tags = ["coreboot", "firmware", "hardware", "laptop", "worklog"]

[extra]
series = "penrose"
part = 1
+++

## The machine

Dell Precision 3520 chassis, mainboard swapped from the stock i7-U board (LA-E151P) to the Xeon one
(LA-E152P: E3-1505M v6, Quadro M620, TB3, ECC RAM). The old board stays in a drawer as the fallback.
Everything below is the Xeon board.

<!-- TODO(owner): prices, links, dates; RAM and clip models -->

| # | Part | Model | Price CHF | Where | Condition | Bought | Installed |
|---|------|-------|-----------|-------|-----------|--------|-----------|
| 1 | Laptop | Dell Precision 3520 (i7-U, LA-E151P) | | | used | | |
| 2 | Mainboard | LA-E152P, E3-1505M v6 + M620 | | | used | 2026-09 | |
| 3 | dGPU cooler | M620 heatsink + pipes | | | used | 2026-09 | |
| 4 | RAM | ECC SO-DIMM | | | | | |
| 5 | SPI programmer | ESP-Prog (FT2232H) | | | | | |
| 6 | SOIC-8 clip | clone | | | new | 2026-09 | |
| 7 | Bench PSU | RD6006, 3.30 V, OCP 0.200 A | | | | | |
| 8 | Thermal pad (CPU/GPU) | Honeywell PTM7950 | | | new | | 2026-10-31 |
| 9 | Thermal putty (VRAM) | Odyssey | | | new | | 2026-10-31 |
| 10 | Adapter | Dell 130 W (DA130PE1-00) | | | | 2026-09 | |

## Benchmarks

One script, same every time: boot, 60 s idle (`turbostat`), `sysbench cpu` 30 s, `sysbench memory`,
then `stress-ng --cpu 8` for 10 minutes with `turbostat` averaged over the run. Kernel 7.2.2-cachyos,
governor `performance` (the first coreboot run, 30.10, was on `powersave`). "Sustained" is the
10-minute average. Bottom cover off from the PTM row through the patched-curve row; not recorded for
the others.

| Firmware / change | Date | Idle W / °C | sysbench ev/s | stress-ng bogo/s | Sustained MHz | °C | Pkg W |
|---|---|---|---|---|---|---|---|
| stock Dell BIOS 1.16.0 | 29.10 | 2.47 / 50 | 7350 | 8573 | 3385 | 76 | 35.24 |
| coreboot, first bootable (cb26) | 30.10 | 1.74 / 44 | 7486 | 8608 | 3365 | 75 | 35.24 |
| coreboot cb32, before teardown | 31.10 | 2.92 / 43 | 7493 | 8289 | 3310 | 74 | 35.21 |
| + fins cleaned, PTM7950, VRAM putty | 31.10 | 2.08 / 47 | 7499 | 8497 | 3358 | 75 | 35.25 |
| + fan held at 4900 rpm | 31.10 | 1.87 / 35 | 7522 | 8771 | 3415 | 69 | 35.24 |
| + fan held at 2500 rpm | 31.10 | 1.67 / 37 | 7518 | 8505 | 3348 | 82 | 35.26 |
| EC loop, stock quiet mode | 31.10 | 2.80 / 47 | 7514 | 8666 | 3374 | 78 | 35.25 |
| EC loop, first patched CPU curve | 31.10 | 2.27 / 47 | 7490 | 8473 | 3351 | 72 | 35.25 |
| + undervolt −50 mV | 31.10 | 2.00 / 45 | 7496 | 8931 | 3509 | 73 | 35.19 |
| + undervolt −90 mV | 31.10 | 1.93 / 45 | 7496 | 9224 | **3600** | 74 | 34.52 |
| + undervolt −80 mV | 31.10 | 1.62 / 42 | 7513 | 9228 | 3594 | 72 | 34.98 |

Three things fall out of this table.

The package power is 35 W in every row: 35.2 ± 0.1 until the undervolt rows. On coreboot the MSR
(`0x610`) and MCHBAR both say PL1 = 45 W, cTDP is off, and the chip still averages 35 W. Dropping the MSR
to 30 W works (29.9 W measured); raising it back to 45 gives a 42 W / 3545 MHz burst and then 34.8 W
again. So there is a second, averaged 35 W limiter above the MSR, most likely the EC over PECI. Stock
does the same: the Dell power profiles (performance / balanced / cool) gave 3390 / 3374 / 3378 MHz at
34.9 W with an identical `0x610`, so they change the fan, not the power.

Cooling buys little. A new thermal interface moved the sustained clock by 48 MHz; pinning the fan at
4900 rpm moved it another 57 for 6 °C, at constant 4900 rpm noise. At a fixed 35 W the chip is
power-bound, not thermally bound.

Undervolting is where the clock comes from. Same 35 W, −90 mV, and the all-core clock sits at exactly
3600 MHz in all sixty 10-second samples. 3600 is the 4-core turbo ratio from `0x1AD`, the ceiling. That
killed the plan to teach the EC a 45 W PL1: there is nothing above 3.6 GHz to spend the watts on.

## Undervolt sweep

Offsets go to core and cache together (they share a rail), first live through MSR `0x150`, then baked
into the coreboot build via the OC mailbox driver as CBFS options. Each step from −60 to −100 passed
15 min of `stress-ng --verify` with no MCE in the journal. Bench reference is the patched-curve row
above.

| Offset | bogo/s | Δ vs 0 | Sustained MHz | Pkg W | Note |
|---|---|---|---|---|---|
| 0 | 8473 | — | 3351 | 35.25 | |
| −50 mV | 8931 | +5.4 % | 3509 | 35.19 | |
| −80 mV | 9228 | +8.9 % | 3594 | 34.98 | on the 35 W edge: 3584–3591 MHz at PkgTmp 78–80 °C, back to 3600 at 75–76 |
| −90 mV | 9224 | +8.9 % | 3600 | 34.52 | 3600 in all 60 samples, ~0.5 W under the limiter |

−80 and −90 perform the same; −90 keeps the margin when the laptop runs hotter (cover on, summer). The
failure point below −100 was never searched: there is no performance left to find there, only a crash.
Settled on −90.

## Fan curve

The EC (MEC5105) keeps its fan tables in the EC region of the same SPI flash: one table per sensor and
thermal mode, six steps each. A step has an rpm, an "up" temperature that moves to the next step and a
"down" temperature that moves back. The fan runs at the highest rpm any sensor asks for. Stock quiet
mode:

| Sensor | 2300 rpm | 3000 rpm | 3700 rpm | 4400 rpm |
|---|---|---|---|---|
| CPU | > 64 °C | > 78 °C | > 94 °C | > 96 °C |
| Skin | > 51 °C | > 65 °C | > 72 °C | > 79 °C |
| Memory | > 40 °C | > 54 °C | > 59 °C | > 61 °C |
| M.2 | > 40 °C | > 55 °C | > 57 °C | > 60 °C |
| GPU | > 58 °C | > 68 °C | > 72 °C | > 76 °C |

The memory and M.2 steps at 40 °C mean the fan never stops: cover on and idle, both sensors sit at
40–52 °C and the fan runs 2300 rpm.

Before rewriting anything, the fan was held at fixed speeds with the EC loop off, cover on, all-core
load at 35 W:

| Held | Result |
|---|---|
| 0 rpm, idle, 10 min | CPU 52–53 °C, every sensor far below its limit |
| 2500 rpm, load | 92 °C at 308 s and still rising, guard stopped it |
| 3000 rpm, load, 10 min | PkgTmp 87–89 °C, flat from ~350 s |
| EC loop, balanced mode | 79–81 °C at ~4370 rpm |

Silent idle is safe, 3000 rpm holds the load, 2500 does not.

The first patch (31.10) changed only the CPU table. The fan stayed off until ~82 °C, but other sensors'
steps then took over: 3000, then 3700 under the long load. The second patch (01.11) is what runs now:

| Sensor | Stock quiet | Now |
|---|---|---|
| CPU | 2300 > 64, 3000 > 78, 3700 > 94, 4400 > 96 | 2500 > 75 (off < 60), 3000 > 84, 3700 > 94, 4400 > 96 |
| Memory | 2300 > 40 (off < 36) | 2300 > 48 (off < 43) |
| M.2 | 2300 > 40 (off < 36) | 2300 > 48 (off < 43) |
| Skin, GPU | | unchanged |

54 bytes in the EC region: 22 in the tables, 32 the payload digest the EC firmware checks.

Run on the patched EC, cover on, quiet mode:

| Phase | Fan | PkgTmp |
|---|---|---|
| Idle, 10 min | 0 rpm the whole time | 49–59 °C |
| Load, 10 min | 2300 → 2500 → 3000 → 3700 in 140 s, then flat 3700 | 86–88 °C, no cycling |
| Cool-down | 3700 → 2300 within 40 s | 55–64 °C |

The 3700 under load comes from the skin sensor (72 °C), not the CPU, whose 3700 step needs 94.

One trap: the EC keeps the thermal mode in battery-backed RAM. Pull the RTC cell (every clip session
does) and it comes back in "balanced", which ignores the quiet tables. coreboot now sends quiet mode to
the EC on every boot.

## Boot time

`systemd-analyze`:

| Firmware | Firmware s | Total s |
|---|---|---|
| stock BIOS | 10.0 | 39.6 |
| coreboot cb26 | 5.5 | 29.8 |
| coreboot cb32, first boot after a full-chip flash | 22.8 | 47.0 |
| coreboot, later boots | 5.2–5.5 | 28.5–31.1 |

The 22.8 s is memory training: the MRC cache is empty after a full-chip flash, every later boot reuses it.

## Images

<!-- TODO: flash chronology; full sha256 -->

| Image | What | sha256 |
|---|---|---|
| stock-xeon-20261029.bin | clip dump of the stock chip, the restore point | 0cbce65a… |
| deguarded-20261029.bin | ME reconfigured with deguard, Boot Guard off | 0c7c9ae3… |
| cb32-live-20261031.bin | coreboot + edk2 | 3133db43… |
| cb32-ecquiet.bin | + first EC patch, CPU table only | 80f5a0ee… |
| ecquiet2-dry.bin | + second EC patch, CPU, memory and M.2 tables | 65f9b5bf… |
