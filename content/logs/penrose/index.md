+++
title = "penrose: coreboot on a Dell Precision 3520 (Xeon board)"
date = 2026-11-01
description = "Worklog for the laptop: the Xeon board swap, what it took to get coreboot on it, and the numbers — ten benchmark runs, an undervolt sweep, and the EC fan curve measured and rewritten."
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

<!-- TODO(owner): prices, links, dates -->

| # | Part | Model | Price CHF | Where | Condition | Bought | Installed |
|---|------|-------|-----------|-------|-----------|--------|-----------|
| 1 | Laptop | Dell Precision 3520 (i7-U, LA-E151P) | | | used | | |
| 2 | Mainboard | LA-E152P, Xeon E3-1505M v6 + M620 | | | used | | |
| 3 | RAM | ECC SO-DIMM ×2 | | | | | |
| 4 | SPI programmer | ESP-Prog (FT2232H) | | | new | | |
| 5 | SOIC-8 clip | | | | new | | |
| 6 | Bench PSU | RD6006 (3.3 V, current limit 300 mA) | | | | | |
| 7 | Thermal pad (CPU/GPU) | Honeywell PTM7950 | | | new | | |
| 8 | Thermal putty (VRAM) | Odyssey | | | new | | |
| 9 | Adapter | Dell 130 W (DA130PE1-00) | | | | | |
| 10 | Dock | TB3 | | | | | |

## Benchmarks

One script, same every time: boot, 60 s idle (`turbostat`), `sysbench cpu` 30 s, `sysbench memory`,
then `stress-ng --cpu 8` for 10 minutes with `turbostat` averaged over the run. Governor `performance`,
kernel 7.2.2-cachyos. "Sustained" is the 10-minute average. Cover on unless noted.

| Firmware / change | Date | Idle W / °C | sysbench ev/s | stress-ng bogo/s | Sustained MHz | °C | Pkg W |
|---|---|---|---|---|---|---|---|
| stock Dell BIOS 1.16.0 | 29.10 | 2.47 / 50 | 7350 | 8573 | 3385 | 76 | 35.24 |
| coreboot, first bootable (cb26) | 30.10 | 1.74 / 44 | 7486 | 8608 | 3365 | 75 | 35.24 |
| coreboot cb32, before teardown | 31.10 | 2.92 / 43 | 7493 | 8289 | 3310 | 74 | 35.21 |
| + fins cleaned, PTM7950, VRAM putty | 31.10 | 2.08 / 47 | 7499 | 8497 | 3358 | 75 | 35.25 |
| + fan held at 2500 rpm | 31.10 | 1.67 / 37 | 7518 | 8505 | 3348 | 82 | 35.26 |
| + fan held at 4900 rpm | 31.10 | 1.87 / 35 | 7522 | 8771 | 3415 | 69 | 35.24 |
| + EC quiet curve (ecquiet) | 31.10 | 2.27 / 47 | 7490 | 8473 | 3351 | 72 | 35.25 |
| + undervolt −50 mV | 31.10 | 2.00 / 45 | 7496 | 8931 | 3509 | 73 | 35.19 |
| + undervolt −80 mV | 31.10 | 1.62 / 42 | 7513 | 9228 | 3594 | 72 | 34.98 |
| + undervolt −90 mV | 31.10 | 1.93 / 45 | 7496 | 9224 | **3600** | 74 | 34.52 |

Three things fall out of this table.

The package power is 35 W in every row. Not 35-ish — 35.2 ± 0.1. The MSR (`0x610`) says PL1 = 45 W on
coreboot, MCHBAR agrees, cTDP is off, and the chip still averages 35 W. Dropping the MSR to 30 W works
(29.9 W measured), raising it to 45 gives a 42 W / 3545 MHz burst for a few seconds and then 34.8 W again.
So there is a second, averaged 35 W limiter above the MSR, most likely the EC over PECI. Stock does the
same; the Dell "performance / balanced / cool" profiles only change the fan, not the power
(3390 / 3374 / 3378 MHz, identical `0x610`).

Cooling buys very little. A new thermal interface moved the sustained clock by 50 MHz; pinning the fan at
4900 rpm moved it another 60 and cost 13 °C of noise. At a fixed 35 W, the chip is power-bound, not
thermally bound.

Undervolting is where the clock comes from. Same 35 W, −90 mV, and the all-core clock sits at exactly
3600 MHz for all sixty 10-second samples. 3600 is the 4-core turbo ratio from `0x1AD` — the ceiling. That
killed the plan to teach the EC a 45 W PL1: there is nothing above 3.6 GHz to spend the watts on.

## Undervolt sweep

Offsets applied to core and cache via the OC mailbox (`DRIVERS_INTEL_OC_MAILBOX` in coreboot,
`CONFIG_INTEL_OC_MAILBOX_ENABLE_UNDERVOLTING=y`). Reference is the ecquiet row above.

| Offset | bogo/s | Δ vs 0 | Sustained MHz | Pkg W | Note |
|---|---|---|---|---|---|
| 0 | 8473 | — | 3351 | 35.25 | |
| −50 mV | 8931 | +5.4 % | 3509 | 35.19 | |
| −80 mV | 9228 | +8.9 % | 3594 | 34.98 | on the 35 W edge: clamps to 3584–3591 when PkgTmp reaches 78–80 °C, back to 3600 at 75 |
| −90 mV | 9224 | +8.9 % | 3600 | 34.52 | flat 3600 × 60 samples, ~0.5 W headroom under the limiter |

−80 and −90 are the same performance; −90 has the margin when the laptop runs hotter (cover on, summer).
The failure point (−110, −150) was never searched — there is no performance left to find, only a crash to
find. Settled on −90.

## Fan curve

The EC fan table lives in the EC region of the same SPI flash, six steps per sensor, each step an
off temperature, an on temperature and an rpm. Stock, CPU sensor:

| Step | rpm | On °C | Off °C |
|---|---|---|---|
| 0 | 0 | 75 | — |
| 1 | 2500 | 78 | 60 |
| 2 | 2500 | 94 | 60 |
| 3 | 3700 | 94 | 85 |
| 4 | 3700 | 96 | 85 |
| 5 | 4400 | 127 | 90 |

Two things wrong with it for a desk machine: the fan starts at 75 °C and, once on, does not stop until
60 — so it never stops; and there is nothing between 2500 and 3700, so under load it bounces between the
two.

Before rewriting it, the fan was held at fixed speeds under 10 min of all-core load (cover on,
EC loop bypassed, guard at PkgTmp 92 / skin 85):

| Held rpm | Result |
|---|---|
| 0 (idle) | 43–47 °C, 2290 rpm on the EC loop — stock never stops the fan |
| 2500 | 90–91 °C after 4 min, guard fires |
| 3000 | plateau 86–88 °C, 571 s of 600 |
| EC loop, stock "balanced" | plateau 80 °C, fan climbs 2700 → 4400 and stays there |
| 4900 | 69 °C sustained |

3000 holds the load; 2500 does not; stock gets there by bouncing off the 3700 step.

The EC runs the fan at the max() over all sensors, and each sensor has its own table per mode
(quiet / balanced / cool). So far this has gone in two rounds.

**Round 1, flashed 31.10** (`cb32-ecquiet`, CPU sensor only, quiet mode): start raised from 75 to 84,
a 3000 step added between 2500 and 3700. On the bench: 0 rpm until PkgTmp ~82, then 2500 — for 35
seconds. After that the fan stepped to 2985 and later 3685, neither of which is in the CPU table any
more: those are the skin and memory sensors' quiet steps taking over the max(). Half a fix.

**Round 2, built 01.11, not flashed** (`ecquiet2`): the same CPU table plus the memory and NGFF
sensors moved one notch later (start 48, stop 43), so the CPU curve actually decides. Target CPU table:

| Step | rpm | On °C | Off °C |
|---|---|---|---|
| 0 | 0 | 75 | — |
| 1 | 2500 | 84 | 60 |
| 2 | 3000 | 94 | 78 |
| 3 | 3700 | 96 | 88 |
| 4 | 3700 | 96 | 88 |
| 5 | 4400 | 127 | 90 |

Step 4 is a copy of 3 (stock pads the same way), step 5 stays as the safety. Pass criterion for the
clip session: 0 rpm at idle with the cover on, no on/off cycling under 10 min of load, PkgTmp ≤ 90.

<!-- TODO: result after the ecquiet2 flash -->

One thing learned the hard way in between: the fan mode (quiet / balanced) lives in the EC's VBAT RAM.
Pull the CMOS cell for a clip session and it silently reverts to balanced — a whole cover-on test run
was measured against the wrong table before anyone noticed. Firmware should set the mode at boot;
that is an open item.

## Boot time

`systemd-analyze`, firmware part only:

| Firmware | Firmware s | Total s |
|---|---|---|
| stock BIOS | 10.0 | 39.6 |
| coreboot cb26 | 5.5 | 29.8 |
| coreboot cb32, first boot after reflash | 22.8 | 47.0 |
| coreboot cb32, cached | 5.2–5.5 | ~29 |

The 22.8 s is one cold memory training (MRC cache empty after a full-chip flash); every boot after is 5 s.

## Images

<!-- TODO: flash chronology with sha256 from recon/xeon -->

| Image | What | sha256 |
|---|---|---|
| stock-xeon-20261029.bin | clip dump of the stock chip, the restore point | |
| deguarded-20261029.bin | ME reconfigured (deguard), Boot Guard off | |
| cb32-live-20261031.bin | coreboot + edk2 | 3133db43… |
| cb32-ecquiet.bin | same + CPU quiet fan curve — **what is on the chip now** | 80f5a0ee… |
| ecquiet2-dry.bin | + mem/NGFF curves, dry build, not flashed | 65f9b5bf… |
