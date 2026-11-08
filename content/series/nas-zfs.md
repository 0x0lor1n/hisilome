+++
title = "Imladris: NAS on ZFS and NixOS"
description = "A home NAS out of an old mATX board: why not a Synology, ZFS on NixOS, an NVMe switch in the x16 slot, 10 Gbit over M.2, and what it all cost."
+++
Three pools on a board from 2016: `tank` on three IronWolf in raidz1, `fast` on three NVMe in raidz1 behind a PCIe switch, `rpool` on a single NVMe on the same switch. Writeups are the decisions and the build; worklogs are the raw lists in between.
