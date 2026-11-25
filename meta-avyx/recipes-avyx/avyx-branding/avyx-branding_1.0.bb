SUMMARY = "AVYX OS branding: logo, wallpapers, os-release extras, issue"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

SRC_URI = " \
    file://avyx-logo.png \
    file://issue \
"
S = "${WORKDIR}"
inherit allarch

do_install() {
    install -d ${D}${datadir}/avyx/branding
    install -m 0644 ${WORKDIR}/avyx-logo.png ${D}${datadir}/avyx/branding/avyx-logo.png
    install -d ${D}${sysconfdir}
    install -m 0644 ${WORKDIR}/issue ${D}${sysconfdir}/issue
}
FILES:${PN} = "${datadir}/avyx ${sysconfdir}/issue"
