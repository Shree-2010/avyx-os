SUMMARY = "AVYX OS boot splash theme for Plymouth (uses the supplied AVYX boot logo)"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

SRC_URI = " \
    file://avyx.plymouth \
    file://avyx.script \
    file://logo.png \
    file://bar-track.png \
    file://bar-fill.png \
    file://bar-glow.png \
"
S = "${WORKDIR}"
inherit allarch

do_install() {
    install -d ${D}${datadir}/plymouth/themes/avyx
    install -m 0644 ${WORKDIR}/avyx.plymouth ${WORKDIR}/avyx.script ${D}${datadir}/plymouth/themes/avyx/
    install -m 0644 ${WORKDIR}/logo.png ${WORKDIR}/bar-track.png ${WORKDIR}/bar-fill.png ${WORKDIR}/bar-glow.png ${D}${datadir}/plymouth/themes/avyx/
}
FILES:${PN} = "${datadir}/plymouth/themes/avyx"
RDEPENDS:${PN} = "plymouth"
