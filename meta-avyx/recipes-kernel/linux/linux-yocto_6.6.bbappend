# AVYX kernel: generic PC hardware (BIOS+UEFI), live-ISO boot essentials built in,
# GPU/Wi-Fi/Bluetooth/audio as modules (firmware is loaded from the real root fs).
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

COMPATIBLE_MACHINE:avyx-x86-64 = "avyx-x86-64"
KMACHINE:avyx-x86-64 = "common-pc-64"
KBRANCH:avyx-x86-64 = "v6.6/standard/base"
SRCREV_machine:avyx-x86-64 = "5ae544e1312ed5b4ed130d22ff1f44333494c4c3"

KERNEL_FEATURES:append:avyx-x86-64 = " cfg/virtio.scc features/drm-bochs/drm-bochs.scc"
SRC_URI:append:avyx-x86-64 = " file://avyx.cfg"
