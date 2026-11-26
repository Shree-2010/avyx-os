SUMMARY = "AVYX OS: live/installable desktop image (labwc + AVYX shell)"
LICENSE = "MIT"

inherit core-image

IMAGE_FEATURES += "splash"
IMAGE_INSTALL = " \
    packagegroup-avyx-base \
    packagegroup-avyx-desktop \
"

# ISO (hybrid BIOS+UEFI): rootfs is a compressed squashfs, RAM overlay added by the initramfs
IMAGE_FSTYPES = "iso"
LIVE_ROOTFS_TYPE = "squashfs-zst"
INITRD_IMAGE_LIVE = "avyx-initramfs"
INITRAMFS_FSTYPES = "cpio.zst"
LABELS_LIVE = "boot"
ROOT_LIVE = "root=/dev/ram0"
APPEND = "ro quiet splash loglevel=3 vt.global_cursor_default=0 console=tty0 console=ttyS0,115200"
GRUB_TIMEOUT = "3"
SYSLINUX_TIMEOUT = "30"
BOOTIMG_VOLUME_ID = "AVYX_LIVE"
EFI_PROVIDER = "grub-efi"

IMAGE_ROOTFS_EXTRA_SPACE = "0"
IMAGE_NAME_SUFFIX = ""
IMAGE_LINGUAS = "en-us en-gb"

# Live user (autologin) and root: password-less for the live session only
inherit extrausers
EXTRA_USERS_PARAMS = " \
    groupadd -f wheel; \
    groupadd -f render; \
    groupadd -f input; \
    groupadd -f plugdev; \
    useradd -m -s /bin/bash -G wheel,video,audio,input,render,plugdev,users avyx; \
    usermod -p '' avyx; \
    usermod -p '*' root; \
"
