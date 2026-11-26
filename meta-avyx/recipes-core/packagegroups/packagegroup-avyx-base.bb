SUMMARY = "AVYX OS: base system (boot, network, audio, storage, tools)"
LICENSE = "MIT"
inherit packagegroup

# these groups name packages that get renamed at packaging time (libdrm -> libdrm2 ...),
# so they cannot be allarch
PACKAGE_ARCH = "${TUNE_PKGARCH}"

RDEPENDS:${PN} = " \
    packagegroup-core-boot \
    kernel-modules \
    linux-firmware \
    systemd-analyze \
    systemd-extra-utils \
    kmod \
    udev-extraconf \
    networkmanager networkmanager-nmcli networkmanager-wifi \
    wpa-supplicant iw wireless-regdb-static \
    bluez5 \
    pipewire pipewire-pulse pipewire-alsa wireplumber \
    alsa-utils alsa-ucm-conf \
    polkit \
    upower \
    dbus \
    shadow sudo util-linux util-linux-mount util-linux-fdisk util-linux-lsblk \
    e2fsprogs e2fsprogs-mke2fs e2fsprogs-e2fsck dosfstools exfatprogs parted \
    rsync zstd xz unzip zip tar \
    squashfs-tools \
    syslinux syslinux-extlinux grub-efi \
    coreutils findutils grep gawk sed less nano procps psmisc \
    iproute2 iputils-ping curl ca-certificates tzdata \
    bash \
    avyx-branding avyx-fonts \
"
