SUMMARY = "Inter typeface (SIL Open Font License 1.1) used as the AVYX UI font"
HOMEPAGE = "https://rsms.me/inter/"
LICENSE = "OFL-1.1"
LIC_FILES_CHKSUM = "file://LICENSE.txt;md5=082d8cc7db39783f598b7eda8c911f9d"

SRC_URI = "https://github.com/rsms/inter/releases/download/v${PV}/Inter-${PV}.zip;subdir=inter"
SRC_URI[sha256sum] = "ff970a5d4561a04f102a7cb781adbd6ac4e9b6c460914c7a101f15acb7f7d1a4"

S = "${WORKDIR}/inter"
inherit allarch fontcache

FONT_PACKAGES = "${PN}"
do_install() {
    install -d ${D}${datadir}/fonts/truetype/inter
    install -m 0644 ${S}/InterVariable.ttf ${S}/InterVariable-Italic.ttf ${D}${datadir}/fonts/truetype/inter/
    for w in Regular Medium SemiBold Bold; do
        install -m 0644 ${S}/extras/ttf/Inter-$w.ttf ${D}${datadir}/fonts/truetype/inter/
    done
}
FILES:${PN} = "${datadir}/fonts"
