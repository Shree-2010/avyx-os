SUMMARY = "AVYX OS: Wayland desktop (labwc compositor + AVYX GTK4 shell and apps)"
LICENSE = "MIT"
inherit packagegroup

RDEPENDS:${PN} = " \
    mesa mesa-megadriver libdrm libinput seatd \
    xkeyboard-config \
    labwc wlroots-0.17 \
    foot grim slurp wl-clipboard swaybg wlr-randr \
    gtk4 gtk4-layer-shell gdk-pixbuf librsvg shared-mime-info adwaita-icon-theme \
    python3-core python3-pygobject python3-pycairo python3-dbus python3-json python3-logging \
    plymouth avyx-plymouth-theme \
    avyx-desktop \
    avyx-session \
"
