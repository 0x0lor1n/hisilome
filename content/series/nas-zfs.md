+++
title = "Custom NAS on ZFS and MSI B250M PRO-VD"
description = "A home NAS out of an old mATX board: why not a Synology, ZFS on NixOS, an NVMe switch in the x16 slot, 10 Gbit over M.2, and what it all cost."
+++
Three pools on a board from 2016: `tank` on three IronWolf in raidz1, `fast` on a pair of NVMe behind a PCIe switch, `rpool` mirrored on a PCIe x1 splitter. Writeups are the decisions and the build; worklogs are the raw lists in between.
