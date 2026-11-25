SUMMARY = "AVYX live-boot initramfs: finds the ISO/USB medium, mounts rootfs.img and adds a RAM overlay"
LICENSE = "MIT"

INITRAMFS_SCRIPTS = " \
    initramfs-framework-base \
    initramfs-module-setup-live \
    initramfs-module-udev \
    initramfs-module-rootfs \
    initramfs-module-avyx-overlay \
"
PACKAGE_INSTALL = "${INITRAMFS_SCRIPTS} ${VIRTUAL-RUNTIME_base-utils} udev base-passwd ${ROOTFS_BOOTSTRAP_INSTALL}"

IMAGE_FEATURES = ""
PACKAGE_EXCLUDE = "kernel-image-*"
IMAGE_NAME_SUFFIX ?= ""
IMAGE_LINGUAS = ""
IMAGE_FSTYPES = "${INITRAMFS_FSTYPES}"
inherit core-image

IMAGE_ROOTFS_SIZE = "8192"
IMAGE_ROOTFS_EXTRA_SPACE = "0"
COMPATIBLE_HOST = "(x86_64.*|i.86.*)-(linux.*)"
