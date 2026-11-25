SUMMARY = "AVYX desktop: shell (top bar, dock, launcher, widgets) and default apps, GTK4 + Python"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

# The sources live in the repository root (src/), shared with the fast UI-preview CI job.
FILESEXTRAPATHS:prepend := "${THISDIR}/../../../src:"
SRC_URI = "file://avyx file://bin file://data"
S = "${WORKDIR}"

inherit python3-dir allarch

do_install() {
    install -d ${D}${PYTHON_SITEPACKAGES_DIR}
    cp -r ${WORKDIR}/avyx ${D}${PYTHON_SITEPACKAGES_DIR}/
    find ${D}${PYTHON_SITEPACKAGES_DIR} -name __pycache__ -prune -exec rm -rf {} +

    install -d ${D}${bindir}
    for f in ${WORKDIR}/bin/*; do install -m 0755 $f ${D}${bindir}/; done

    install -d ${D}${datadir}
    cp -r ${WORKDIR}/data/share/* ${D}${datadir}/
}

FILES:${PN} = "${PYTHON_SITEPACKAGES_DIR}/avyx ${bindir} ${datadir}"

RDEPENDS:${PN} = " \
    python3-core python3-modules python3-pygobject python3-pycairo \
    gtk4 gtk4-layer-shell gdk-pixbuf pango glib-2.0 librsvg \
    adwaita-icon-theme shared-mime-info xdg-user-dirs \
    systemd networkmanager-nmcli upower \
    avyx-branding avyx-fonts \
"
