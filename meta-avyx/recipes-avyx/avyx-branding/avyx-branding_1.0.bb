SUMMARY = "AVYX OS branding: logo and brand assets (/etc/issue comes from base-files via DISTRO_NAME)"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

SRC_URI = " \
    file://avyx-logo.png \
"
S = "${WORKDIR}"
inherit allarch

do_install() {
    install -d ${D}${datadir}/avyx/branding
    install -m 0644 ${WORKDIR}/avyx-logo.png ${D}${datadir}/avyx/branding/avyx-logo.png
}
FILES:${PN} = "${datadir}/avyx"
