# AVYX: only the script theme engine (our theme) plus text/details fallbacks; no dracut initrd helper.
PLYMOUTH_THEMES = "script text details"
PACKAGECONFIG:remove = "initrd"
PLYMOUTH_BACKGROUND_COLOR = "0x000000"
PLYMOUTH_BACKGROUND_START_COLOR_STOP = "0x000000"
PLYMOUTH_BACKGROUND_END_COLOR_STOP = "0x000000"

# Select the AVYX theme: replace the stock /etc/plymouth/plymouthd.conf (a single owner avoids an opkg file clash)
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://plymouthd.conf"
do_install:append() {
    install -d ${D}${sysconfdir}/plymouth
    install -m 0644 ${WORKDIR}/plymouthd.conf ${D}${sysconfdir}/plymouth/plymouthd.conf
}
