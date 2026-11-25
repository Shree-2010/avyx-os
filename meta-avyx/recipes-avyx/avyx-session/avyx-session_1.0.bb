SUMMARY = "AVYX OS session glue: labwc configuration, session launcher, autologin, CI markers"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

SRC_URI = " \
    file://avyx-session \
    file://avyx-mark \
    file://avyx-boot-marker \
    file://avyx-session.sh \
    file://labwc/rc.xml \
    file://labwc/menu.xml \
    file://labwc/themerc \
    file://labwc/autostart \
    file://systemd/avyx-boot-marker.service \
    file://systemd/autologin.conf \
    file://50-avyx.rules \
    file://avyx-live.conf \
"
S = "${WORKDIR}"
inherit systemd allarch

SYSTEMD_SERVICE:${PN} = "avyx-boot-marker.service"
SYSTEMD_AUTO_ENABLE = "enable"

do_install() {
    install -d ${D}${bindir} ${D}${datadir}/avyx/labwc ${D}${sysconfdir}/profile.d
    install -m 0755 ${WORKDIR}/avyx-session ${D}${bindir}/avyx-session
    install -m 0755 ${WORKDIR}/avyx-mark ${D}${bindir}/avyx-mark
    install -d ${D}${libexecdir}/avyx
    install -m 0755 ${WORKDIR}/avyx-boot-marker ${D}${libexecdir}/avyx/avyx-boot-marker
    install -m 0644 ${WORKDIR}/avyx-session.sh ${D}${sysconfdir}/profile.d/avyx-session.sh
    install -m 0644 ${WORKDIR}/labwc/rc.xml ${WORKDIR}/labwc/menu.xml ${D}${datadir}/avyx/labwc/
    install -d ${D}${datadir}/themes/AVYX/labwc
    install -m 0644 ${WORKDIR}/labwc/themerc ${D}${datadir}/themes/AVYX/labwc/themerc
    install -m 0755 ${WORKDIR}/labwc/autostart ${D}${datadir}/avyx/labwc/autostart

    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/systemd/avyx-boot-marker.service ${D}${systemd_system_unitdir}/
    # live session: auto-login on tty1
    install -d ${D}${systemd_system_unitdir}/getty@tty1.service.d
    install -m 0644 ${WORKDIR}/systemd/autologin.conf ${D}${systemd_system_unitdir}/getty@tty1.service.d/autologin.conf

    install -d ${D}${sysconfdir}/polkit-1/rules.d
    install -m 0644 ${WORKDIR}/50-avyx.rules ${D}${sysconfdir}/polkit-1/rules.d/50-avyx.rules
    install -d ${D}${sysconfdir}/avyx
    install -m 0644 ${WORKDIR}/avyx-live.conf ${D}${sysconfdir}/avyx/live.conf
}

FILES:${PN} = " \
    ${bindir} ${libexecdir}/avyx ${datadir}/avyx/labwc ${datadir}/themes/AVYX ${sysconfdir} ${systemd_system_unitdir} \
"
RDEPENDS:${PN} = "labwc dbus util-linux-agetty bash polkit avyx-desktop"

SRC_URI += "file://avyx-tmpfiles.conf"
do_install:append() {
    install -d ${D}${libdir}/tmpfiles.d
    install -m 0644 ${WORKDIR}/avyx-tmpfiles.conf ${D}${libdir}/tmpfiles.d/avyx.conf
}
FILES:${PN} += "${libdir}/tmpfiles.d/avyx.conf"
