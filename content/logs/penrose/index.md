+++
title = "A coding terminal in a Dell Latitude 5580 chassis"
date = 2026-11-01
description = "A 2017 Latitude chassis around the Precision 3520 Xeon board: parts, benchmarks, undervolt, EC fan curve."

[taxonomies]
tags = ["coreboot", "firmware", "hardware", "laptop", "worklog"]

[extra]
series = "penrose"
part = 1
+++

## The machine

Dell Latitude 5580, mainboard swapped from the stock i7-U board (LA-E151P) to the Precision 3520 Xeon one
(LA-E152P: E3-1505M v6, Quadro M620, TB3, ECC RAM). Everything below is the Xeon board.
coreboot here is the tool, not the goal: it is how the hardware gets tuned to its limit.

| # | Part | Model | Price CHF | Where | Condition | Bought | Installed |
|---|------|-------|-----------|-------|-----------|--------|-----------|
| 1 | Laptop | Dell Latitude 5580 | 50 | Work write-off | used | 06.01.2020 | - |
| 2 | Motherboard | [LA-E152P](https://de.aliexpress.com/item/1005011773147370.html) | 55.47 | AliExpress | refurbished | 07.09.2026 | 28.10.2026 |
| 3 | CPU cooler | [Dell 03NDV7](https://de.aliexpress.com/item/1005012739349633.html) | 35.00 | AliExpress | new | 07.09.2026 | 28.10.2026 |
| 4 | Battery | [Dell GJKNX](https://de.aliexpress.com/item/1005013221596137.html) | 35.59 | AliExpress | new old stock | 22.09.2026 | 28.10.2026 |
| 5 | PSU | Dell DA130PE1-00 | 30 | Ricardo.ch | used | 07.09.2026 | 28.10.2026 |
| 6 | SSD | [Lexar NS100 1 TB](https://www.amazon.fr/dp/B07YXML7KG) | 120 | Amazon.fr | new | 12.10.2026 | 12.10.2026 |
| 7 | Mount | SSD caddy | 6.15 | AliExpress | new | 22.09.2026 | - |
| 8 | Pads | Honeywell PTM7950 40x80 mm | 6.96 | AliExpress | new | - | 31.10.2026 |
| 9 | Putty | Odyssey 1.5 mm | 2.96 | AliExpress | new | - | 31.10.2026 |
| 10 | Wi-Fi | [MediaTek MT7925](https://de.aliexpress.com/item/1005010105899192.html) | 20.79 | AliExpress | new | 22.09.2026 | - |
| 11 | RAM | [2x MEM-Store 32 GB PC4-19200S ECC](https://www.ebay.com/itm/325834830265) | 356 | eBay | refurbished | Planned | - |
| 12 | eGPU adapter | [M.2 → OCuLink](https://de.aliexpress.com/item/1005007551135681.html) | 15.82 | AliExpress | new | Planned | - |

**Total: CHF 735**

## Not in the build

### Firmware tooling

| # | Part | Model | Price CHF | Where |
|---|------|-------|-----------|-------|
| C1 | SPI programmer | ESP-Prog (FT2232H) | - | had it |
| C2 | SOIC-8 clip | [SOIC-8 clip 5250](https://de.aliexpress.com/item/1005008339879712.html) | 7.35 | AliExpress |
| C3 | Bench PSU | RD6006 | - | had it |
| C4 | Flasher | [spi-clip-rig](https://github.com/0x0lor1n/spi-clip-rig) | - | GitHub |
| C5 | Firmware | [coreboot + edk2 build](https://github.com/0x0lor1n/the-hive/tree/main/cells/wintermute) | - | GitHub |

### Written off

| # | Part | Model | Price CHF | Where | Condition | Bought | Installed | Replaced | Cause |
|---|------|-------|-----------|-------|-----------|--------|-----------|----------|-------|
| W1 | SSD | [Crucial P3 1 TB](https://www.galaxus.ch/en/s1/product/crucial-p3-1000-gb-m2-2280-ssd-21575420) | 59.90 | Galaxus.ch | new | 27.02.2025 | - | 12.10.2026 | M.2 slot freed |
| W2 | Motherboard | LA-E151P (i7-U) | - | with the laptop | used | 06.01.2020 | - | 28.10.2026 | Upgraded |
| W3 | CPU cooler | stock heatsink + fan | - | with the laptop | used | 06.01.2020 | - | 28.10.2026 | Upgraded |
| W4 | PSU | Dell 0G4X7T | - | with the laptop | used | 06.01.2020 | - | 28.10.2026 | Decommissioned |

## Benchmarks

Same script every run: 60 s idle, `sysbench cpu` 30 s, `sysbench memory`, then `stress-ng --cpu 8` for
10 minutes. "Sustained" is the 10-minute average. Kernel 7.2.2-cachyos, governor `performance` (the first
coreboot run was on `powersave`). Bottom cover off from the PTM row through the patched-curve row.

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

Package power is 35 W in every row, on stock and on coreboot alike. The firmware asks for 45 W; a second
limiter above the CPU, most likely the EC, holds the average at 35. Dell's power profiles change the fan,
not the power.

Cooling buys little: a new thermal interface gave +48 MHz, the fan pinned at 4900 rpm another +57.
At a fixed 35 W the chip is power-bound, not thermally bound.

## Undervolt

Undervolting is where the clock comes from. At −90 mV the all-core clock sits at 3600 MHz, the turbo
ceiling, in every sample of the 10-minute run, still inside 35 W. That also ended the plan to unlock 45 W:
there is nothing above 3.6 GHz to spend it on.

The offset is baked into the firmware and applies from power-on. Every 10 mV step down to −100 passed
15 min of `stress-ng --verify`. −80 performs the same as −90, but already touches the 35 W limit at
78–80 °C; −90 keeps the margin for a closed cover in summer.

## Fan curve

The EC keeps its fan tables in the same SPI flash as the firmware: per sensor, temperature steps to rpm.
The fan follows whichever sensor asks for the most. In stock quiet mode the memory and M.2 sensors start
the fan at 40 °C, so it never stops.

The fan held at fixed speeds first, EC loop off, cover on, load at 35 W:

| Held | Result |
|---|---|
| 0 rpm, idle, 10 min | CPU 52–53 °C, every sensor far below its limit |
| 2500 rpm, load | 92 °C at 308 s and still rising, guard stopped it |
| 3000 rpm, load, 10 min | PkgTmp 87–89 °C, flat from ~350 s |
| EC loop, balanced mode | 79–81 °C at ~4370 rpm |

Rewritten tables, live since 01.11 (the first attempt, CPU table only, let the other sensors take over):

| Sensor | Stock quiet | Now |
|---|---|---|
| CPU | 2300 > 64, 3000 > 78, 3700 > 94, 4400 > 96 | 2500 > 75 (off < 60), 3000 > 84, 3700 > 94, 4400 > 96 |
| Memory | 2300 > 40 (off < 36) | 2300 > 48 (off < 43) |
| M.2 | 2300 > 40 (off < 36) | 2300 > 48 (off < 43) |
| Skin, GPU | | unchanged |

On the patched EC, cover on:

| Phase | Fan | PkgTmp |
|---|---|---|
| Idle, 10 min | 0 rpm the whole time | 49–59 °C |
| Load, 10 min | 2300 → 2500 → 3000 → 3700 in 140 s, then flat 3700 | 86–88 °C, no cycling |
| Cool-down | 3700 → 2300 within 40 s | 55–64 °C |

The 3700 under load comes from the skin sensor (72 °C step), not the CPU. The EC forgets the mode with
the RTC cell, so the firmware sets quiet on every boot. Table layout and the patch:
[cells/wintermute](https://github.com/0x0lor1n/the-hive/tree/main/cells/wintermute).

## Boot time

`systemd-analyze`:

| Firmware | Firmware s | Total s |
|---|---|---|
| stock BIOS | 10.0 | 39.6 |
| coreboot cb26 | 5.5 | 29.8 |
| coreboot cb32, first boot after a full-chip flash | 22.8 | 47.0 |
| coreboot, later boots | 5.2–5.5 | 28.5–31.1 |

The 22.8 s is memory training after a full-chip flash; later boots reuse the cache.

## Evolution of Firmware Images

| Step | Image |
|---|---|
| 29.10 | clip dump of the stock chip, the restore point |
| 29.10 | Intel ME reconfigured with deguard, Boot Guard off: without this the board runs only Dell-signed firmware |
| 31.10 | coreboot + edk2 |
| 31.10 | + EC fan tables, CPU only |
| 01.11 | + EC fan tables, CPU, memory and M.2 (live) |
