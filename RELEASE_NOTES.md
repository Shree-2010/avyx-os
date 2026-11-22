# AVYX OS 0.1.0-dev+15

- ISO size: 1616 MB
- SHA256: `6e9aa1d57962c572f6841c87171abcbd2b8d6a5eb130f57ae4c01e37d37a19eb`

## Measured in CI (QEMU, 2 vCPU, 4 GB RAM, emulated Sandy Bridge CPU, std VGA = software rendering)

| Check | UEFI | BIOS |
|---|---|---|
| Boots to the system (multi-user) | PASS | PASS |
| Desktop shell started (plasmashell) | PASS | PASS |
| Seconds from power-on to multi-user (includes bootloader menu) | 15.1 s | 13.1 s |
| Seconds from power-on to desktop shell | 18.6 s | 16.1 s |
| RAM used at idle (MB, after 60 s settle) | 1057 | 1045 |
| Accelerator | kvm | kvm |

## Installation to disk (Calamares, UEFI, 20 GB virtual disk, driven in CI)

| Check | Result |
|---|---|
| Live desktop started before installing | PASS |
| Installer ran to the end of its install steps | PASS |
| Installed disk boots on its own (no ISO) to the desktop | PASS |
| Installed system runs from the disk (not the live image) | PASS |
| RAM used at idle on the installed system (MB) | 999 |

## Not verified in this build

Everything not listed as PASS above was not tested: Wi-Fi/Bluetooth on real hardware, suspend/resume, hardware video decode,
Windows/Android app support, Secure Boot (the ISO and installed system are not signed), BIOS-mode installs, dual-boot,
and behaviour on real old laptops.

## Licensing

AVYX-original code and art: MIT / CC0. All other software keeps its own license (see /usr/share/doc/*/copyright in the image).
GPL source: the exact package list is in `packages.txt`; sources are available from the Debian archive (deb.debian.org / snapshot.debian.org).
Based on Debian GNU/Linux; AVYX OS is not affiliated with or endorsed by the Debian project.
