SUMMARY = "AVYX initramfs module: writable RAM overlay on top of the read-only live rootfs"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"
RDEPENDS:${PN} = "initramfs-framework-base initramfs-module-rootfs"

inherit allarch

SRC_URI = "file://avyx-overlay"
S = "${WORKDIR}"

do_install() {
    install -d ${D}/init.d
    # runs after 90-rootfs (mounts rootfs.img) and before 99-finish (switch_root)
    install -m 0755 ${WORKDIR}/avyx-overlay ${D}/init.d/91-avyx-overlay
}

FILES:${PN} = "/init.d/91-avyx-overlay"
