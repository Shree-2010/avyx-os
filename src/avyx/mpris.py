"""Minimal MPRIS client: follows the most relevant media player on the session bus."""
import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

PREFIX = "org.mpris.MediaPlayer2."
OBJ = "/org/mpris/MediaPlayer2"
IFACE = PREFIX + "Player"


class Mpris:
    def __init__(self, on_change):
        self.on_change = on_change
        self.proxy = None
        self.name = None
        self.title = ""
        self.artist = ""
        self.status = "Stopped"
        self.art = None
        try:
            self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error:
            self.bus = None
            return
        self.bus.signal_subscribe("org.freedesktop.DBus", "org.freedesktop.DBus", "NameOwnerChanged",
                                  "/org/freedesktop/DBus", None, Gio.DBusSignalFlags.NONE, self._owner_changed)
        GLib.idle_add(self._scan)

    def _scan(self):
        try:
            r = self.bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "ListNames",
                                   None, GLib.VariantType("(as)"), Gio.DBusCallFlags.NONE, 1000, None)
            names = [n for n in r.unpack()[0] if n.startswith(PREFIX)]
        except GLib.Error:
            names = []
        if self.name not in names:
            self._detach()
        if names and not self.proxy:
            self._attach(names[0])
        return False

    def _owner_changed(self, conn, sender, path, iface, signal, params):
        name = params.unpack()[0]
        if name.startswith(PREFIX):
            GLib.idle_add(self._scan)

    def _attach(self, name):
        try:
            self.proxy = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None, name, OBJ, IFACE, None)
        except GLib.Error:
            self.proxy = None
            return
        self.name = name
        self.proxy.connect("g-properties-changed", lambda *a: self._refresh())
        self._refresh()

    def _detach(self):
        self.proxy = None
        self.name = None
        self.title = self.artist = ""
        self.status = "Stopped"
        self.art = None
        self.on_change()

    def _refresh(self):
        if not self.proxy:
            return
        md = self.proxy.get_cached_property("Metadata")
        st = self.proxy.get_cached_property("PlaybackStatus")
        self.status = st.get_string() if st else "Stopped"
        self.title = self.artist = ""
        self.art = None
        if md:
            d = md.unpack()
            self.title = d.get("xesam:title", "") or ""
            a = d.get("xesam:artist", "")
            self.artist = ", ".join(a) if isinstance(a, (list, tuple)) else (a or "")
            url = d.get("mpris:artUrl", "")
            if isinstance(url, str) and url.startswith("file://"):
                self.art = url[7:]
        self.on_change()

    def call(self, method):
        if self.proxy:
            self.proxy.call(method, None, Gio.DBusCallFlags.NONE, 1000, None, None, None)

    def play_pause(self):
        self.call("PlayPause")

    def next(self):
        self.call("Next")

    def previous(self):
        self.call("Previous")
