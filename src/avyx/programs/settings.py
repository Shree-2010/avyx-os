"""AVYX Settings: network, Bluetooth, display, sound, appearance, location, power, about."""
import json
import os
import re
import subprocess
import sys
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gio, GLib, Gtk  # noqa: E402

from .. import appkit, apps, config, sysinfo  # noqa: E402
from ..appkit import AppWindow  # noqa: E402
from ..gfx import Glyph  # noqa: E402

px = config.px


def run_async(argv, cb, timeout=25):
    """Run a command in a thread; cb(returncode, stdout) is called on the main loop."""
    def work():
        try:
            p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
            res = (p.returncode, p.stdout)
        except (OSError, subprocess.SubprocessError):
            res = (127, "")
        GLib.idle_add(lambda: (cb(*res), False)[1])
    threading.Thread(target=work, daemon=True).start()


def ctl(cmd):
    config.spawn(["avyx-ctl", cmd])


def label(text, css=None, xalign=0.0, wrap=False):
    lab = Gtk.Label(label=text, xalign=xalign)
    if css:
        lab.add_css_class(css)
    if wrap:
        lab.set_wrap(True)
    return lab


def row(title, widget=None, sub=None):
    r = Gtk.Box(spacing=px(14))
    r.add_css_class("set-row")
    tv = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, valign=Gtk.Align.CENTER)
    tv.append(label(title))
    if sub:
        tv.append(label(sub, "sub", wrap=True))
    r.append(tv)
    if widget is not None:
        widget.set_valign(Gtk.Align.CENTER)
        r.append(widget)
    return r


def group(*rows):
    g = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    g.add_css_class("set-group")
    g.set_margin_bottom(px(16))
    for r in rows:
        g.append(r)
    return g


def page_box(title):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box.set_margin_start(px(28))
    box.set_margin_end(px(28))
    box.set_margin_top(px(22))
    box.set_margin_bottom(px(22))
    t = label(title, "set-title")
    box.append(t)
    return box


def switch(active, cb):
    s = Gtk.Switch()
    s.set_active(active)
    s.connect("notify::active", lambda sw, _p: cb(sw.get_active()))
    return s


def btn(text, cb, primary=False):
    b = Gtk.Button(label=text)
    b.add_css_class("btn")
    if primary:
        b.add_css_class("primary")
    b.connect("clicked", lambda *_: cb())
    return b


# ------------------------------------------------------------------------------------------ pages
class NetworkPage:
    def __init__(self, win):
        self.win = win
        self.box = page_box("Wi-Fi & Network")
        self.status = label("Checking…", "sub")
        self.listbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.listbox.add_css_class("set-group")
        self.sw = Gtk.Switch()
        self.sw.connect("notify::active", self._toggle)
        self._updating = False
        head = group(row("Wi-Fi", self.sw, "Turn the wireless radio on or off"), row("Connection", self.status))
        self.box.append(head)
        bar = Gtk.Box(spacing=px(8))
        bar.set_margin_bottom(px(8))
        bar.append(label("Available networks", "dim-label"))
        sp = Gtk.Box(hexpand=True)
        bar.append(sp)
        bar.append(btn("Scan", self.scan))
        self.box.append(bar)
        self.box.append(self.listbox)
        self.refresh()

    def refresh(self):
        def got(rc, out):
            if rc == 127:
                self.status.set_label("NetworkManager isn't available")
                return
            self._updating = True
            self.sw.set_active(out.strip() == "enabled")
            self._updating = False
        run_async(["nmcli", "radio", "wifi"], got)
        run_async(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "dev"], self._dev)
        self.scan()

    def _dev(self, rc, out):
        lines = []
        for ln in out.splitlines():
            p = ln.split(":")
            if len(p) >= 4 and p[1] in ("wifi", "ethernet") and p[2] == "connected":
                lines.append("%s: %s" % ("Wi-Fi" if p[1] == "wifi" else "Ethernet", p[3]))
        self.status.set_label(", ".join(lines) if lines else "Not connected")

    def _toggle(self, sw, _p):
        if self._updating:
            return
        run_async(["nmcli", "radio", "wifi", "on" if sw.get_active() else "off"], lambda *_: GLib.timeout_add(1500, lambda: (self.scan(), False)[1]))

    def scan(self):
        run_async(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "dev", "wifi", "list", "--rescan", "auto"], self._scan_done)

    def _scan_done(self, rc, out):
        c = self.listbox.get_first_child()
        while c is not None:
            n = c.get_next_sibling()
            self.listbox.remove(c)
            c = n
        seen = set()
        for ln in out.splitlines():
            p = re.split(r"(?<!\\):", ln)
            if len(p) < 4:
                continue
            inuse, ssid, sig, sec = p[0].strip(), p[1].replace("\\:", ":"), p[2], p[3]
            if not ssid or ssid in seen:
                continue
            seen.add(ssid)
            b = btn("Connected" if inuse == "*" else "Connect", lambda s=ssid, se=sec: self.connect_to(s, se))
            sub = "%s%%  %s" % (sig, "Secured" if sec and sec != "--" else "Open")
            self.listbox.append(row(ssid, b, sub))
        if not seen:
            self.listbox.append(row("No networks found" if rc != 127 else "No Wi-Fi hardware detected", None, "Is the radio on?"))

    def connect_to(self, ssid, sec):
        def go(pw=None):
            cmd = ["nmcli", "dev", "wifi", "connect", ssid] + (["password", pw] if pw else [])
            run_async(cmd, lambda rc, out: (self.refresh(), appkit.message(self.win, "Could not connect", out or "Check the password and try again.") if rc != 0 else None), 40)
        if sec and sec != "--":
            appkit.prompt(self.win, "Password for “%s”" % ssid, "", "Connect", go)
        else:
            go()


class DisplayPage:
    def __init__(self, win):
        self.win = win
        self.box = page_box("Display")
        self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box.append(self.holder)
        run_async(["wlr-randr"], self._got)

    def _got(self, rc, out):
        if rc != 0 or not out.strip():
            self.holder.append(group(row("Display information isn't available", None, "wlr-randr could not talk to the compositor.")))
            return
        outputs, cur = [], None
        for ln in out.splitlines():
            if ln and not ln.startswith(" "):
                cur = {"name": ln.split()[0], "desc": ln[len(ln.split()[0]):].strip().strip('"'), "modes": [], "current": None}
                outputs.append(cur)
            elif cur is not None:
                m = re.match(r"\s+(\d+x\d+) px, ([\d.]+) Hz(.*)", ln)
                if m:
                    mode = "%s@%s" % (m.group(1), m.group(2))
                    cur["modes"].append(mode)
                    if "current" in m.group(3):
                        cur["current"] = mode
        for o in outputs:
            dd = Gtk.DropDown.new_from_strings(o["modes"] or ["Automatic"])
            if o["current"] in o["modes"]:
                dd.set_selected(o["modes"].index(o["current"]))
            apply_b = btn("Apply", lambda o=o, d=dd: self.apply(o, d), True)
            apply_b.set_sensitive(bool(o["modes"]))
            box = Gtk.Box(spacing=px(8))
            box.append(dd)
            box.append(apply_b)
            self.holder.append(group(row(o["name"], None, o["desc"]), row("Resolution & refresh rate", box)))
        self.holder.append(label("The desktop restarts briefly when the resolution changes.", "sub"))

    def apply(self, o, dd):
        modes = o["modes"]
        if not modes:
            return
        mode = modes[dd.get_selected()]
        run_async(["wlr-randr", "--output", o["name"], "--mode", mode], lambda rc, out: ctl("restart"))


class SoundPage:
    def __init__(self, win):
        self.win = win
        self.box = page_box("Sound")
        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.scale.add_css_class("cc")
        self.scale.set_size_request(px(260), -1)
        self.scale.set_draw_value(False)
        self.mute = Gtk.Switch()
        self._upd = False
        self.box.append(group(row("Output volume", self.scale), row("Mute", self.mute)))
        self.scale.connect("value-changed", self._vol)
        self.mute.connect("notify::active", lambda sw, _p: None if self._upd else sysinfo.toggle_mute())
        self.note = label("", "sub")
        self.box.append(self.note)
        threading.Thread(target=lambda: GLib.idle_add(self._got, sysinfo.volume()), daemon=True).start()

    def _got(self, v):
        if not v:
            self.note.set_label("No audio server found (WirePlumber). Sound controls are unavailable.")
            return False
        self._upd = True
        self.scale.set_value(v[0] * 100)
        self.mute.set_active(v[1])
        self._upd = False
        return False

    def _vol(self, sc):
        if not self._upd:
            sysinfo.set_volume(sc.get_value() / 100.0)


class AppearancePage:
    def __init__(self, win):
        self.win = win
        s = config.settings
        self.box = page_box("Appearance")
        self.box.append(group(
            row("Dock magnification", switch(bool(s.get("magnify", True)), lambda v: self.set("magnify", v)), "Icons grow as the pointer moves over the dock"),
            row("Desktop widgets", switch(bool(s.get("widgets", True)), lambda v: self.set("widgets", v)), "Clock, media, system monitor"),
            row("24-hour clock", switch(bool(s.get("clock24", False)), lambda v: self.set("clock24", v)))))
        self.box.append(label("Wallpaper", "dim-label"))
        self.box.append(group(row("Choose a picture…", btn("Browse", self.choose), "JPEG or PNG; it is scaled to fill the screen"),
                              row("Use the AVYX default", btn("Reset", lambda: self.set("wallpaper", None), True))))

    def set(self, k, v):
        config.settings.set(k, v)
        ctl("reload")

    def choose(self):
        dlg = Gtk.FileDialog()
        flt = Gtk.FileFilter()
        flt.set_name("Images")
        flt.add_mime_type("image/jpeg")
        flt.add_mime_type("image/png")
        flts = Gio.ListStore.new(Gtk.FileFilter)
        flts.append(flt)
        dlg.set_filters(flts)

        def done(d, res):
            try:
                f = d.open_finish(res)
                self.set("wallpaper", f.get_path())
            except GLib.Error:
                pass
        dlg.open(self.win, None, done)


class LocationPage:
    def __init__(self, win):
        self.win = win
        self.box = page_box("Location")
        loc = config.settings.get("location") or {}
        self.name = Gtk.Entry()
        self.name.add_css_class("field")
        self.name.set_text(loc.get("name", ""))
        self.name.set_placeholder_text("City, Country")
        self.lat = Gtk.Entry()
        self.lat.add_css_class("field")
        self.lat.set_text(str(loc.get("lat", "")))
        self.lat.set_placeholder_text("e.g. 13.0827")
        self.lon = Gtk.Entry()
        self.lon.add_css_class("field")
        self.lon.set_text(str(loc.get("lon", "")))
        self.lon.set_placeholder_text("e.g. 80.2707")
        self.box.append(group(row("Place name", self.name), row("Latitude", self.lat), row("Longitude", self.lon)))
        self.box.append(label("Used only for the desktop weather widget. Weather is fetched from open-meteo.com when you are online; nothing is sent until you save a location here.", "sub", wrap=True))
        b = btn("Save", self.save, True)
        b.set_halign(Gtk.Align.START)
        b.set_margin_top(px(12))
        self.box.append(b)

    def save(self):
        try:
            lat, lon = float(self.lat.get_text()), float(self.lon.get_text())
        except ValueError:
            appkit.message(self.win, "Invalid coordinates", "Enter latitude and longitude as decimal numbers.")
            return
        config.settings.set("location", {"name": self.name.get_text().strip() or "My location", "lat": lat, "lon": lon})
        ctl("restart")


class PowerPage:
    def __init__(self, win):
        self.box = page_box("Power & Battery")
        b = sysinfo.battery()
        if b:
            self.box.append(group(row("Battery", label("%d%%" % b[0]), "Charging" if b[1] else "On battery")))
        else:
            self.box.append(group(row("No battery detected", None, "This computer runs on mains power.")))
        self.box.append(group(row("Restart", btn("Restart", lambda: ctl("reboot"))), row("Shut down", btn("Shut Down", lambda: ctl("poweroff")))))


class AboutPage:
    def __init__(self, win):
        self.box = page_box("About AVYX OS")
        top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign=Gtk.Align.CENTER, spacing=px(4))
        top.set_margin_bottom(px(18))
        top.append(apps.icon_widget("avyx-mark", px(88)))
        t = label("AVYX OS", "big-quote", xalign=0.5)
        t.set_margin_top(px(8))
        top.append(t)
        top.append(label("BUILD BEYOND LIMITS", "dim-label", xalign=0.5))
        self.box.append(top)
        ver = "0.1.0"
        try:
            with open("/etc/os-release") as f:
                for ln in f:
                    if ln.startswith("VERSION_ID="):
                        ver = ln.split("=", 1)[1].strip().strip('"')
        except OSError:
            pass
        cpu = "unknown"
        try:
            with open("/proc/cpuinfo") as f:
                for ln in f:
                    if ln.lower().startswith("model name"):
                        cpu = ln.split(":", 1)[1].strip()
                        break
        except OSError:
            pass
        gfx = config.profile()
        mem = sysinfo.mem_percent()
        disk = sysinfo.disk_percent("/")
        rows = [("Version", ver), ("Kernel", os.uname().release), ("Processor", cpu), ("Memory", sysinfo.human(mem[1])),
                ("Disk", "%s used of %s" % (sysinfo.human(disk[2]), sysinfo.human(disk[1]))), ("Graphics profile", gfx.capitalize())]
        self.box.append(group(*[row(k, label(v, "dim-label")) for k, v in rows]))
        self.box.append(label("AVYX OS is built with the Yocto Project, labwc and GTK4. Most components are free software; their licences and source offers are on the installation media (/usr/share/licenses).", "sub", wrap=True))


PAGES = [("network", "Wi-Fi & Network", "wifi", NetworkPage), ("display", "Display", "window", DisplayPage), ("sound", "Sound", "volume", SoundPage),
         ("appearance", "Appearance", "sun", AppearancePage), ("location", "Location", "pin", LocationPage), ("power", "Power", "battery", PowerPage),
         ("about", "About", "info", AboutPage)]


class SettingsWindow(AppWindow):
    def __init__(self, app, page="network"):
        super().__init__(app, "Settings", 900, 620)
        t = Gtk.Label(label="Settings", xalign=0, hexpand=True)
        t.add_css_class("app-title")
        t.set_margin_start(px(8))
        self.header_append(t)
        main = Gtk.Box(vexpand=True)
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(2))
        side.add_css_class("set-side")
        side.set_size_request(px(220), -1)
        self.btns = {}
        for pid, name, glyph, cls in PAGES:
            b = Gtk.Button()
            b.add_css_class("side")
            r = Gtk.Box(spacing=px(11))
            r.append(Glyph(glyph, px(18)))
            r.append(Gtk.Label(label=name, xalign=0))
            b.set_child(r)
            b.connect("clicked", lambda _b, p=pid: self.show(p))
            side.append(b)
            self.btns[pid] = b
        main.append(side)
        self.scroll = Gtk.ScrolledWindow(hexpand=True)
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        main.append(self.scroll)
        self.body.append(main)
        self.show(page if page in self.btns else "network")

    def show(self, pid):
        for k, b in self.btns.items():
            (b.add_css_class if k == pid else b.remove_css_class)("sel")
        cls = {p[0]: p[3] for p in PAGES}[pid]
        self.scroll.set_child(cls(self).box)


class SettingsApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.avyx.Settings", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.page = "network"

    def do_startup(self):
        Gtk.Application.do_startup(self)
        appkit.setup_env()

    def do_command_line(self, cl):
        args = cl.get_arguments()[1:]
        self.page = args[0].split(":")[-1] if args else "network"
        self.activate()
        return 0

    def do_activate(self):
        w = self.get_active_window()
        if w:
            w.show(self.page)
            w.present()
        else:
            SettingsWindow(self, self.page).present()


def main(argv):
    return SettingsApp().run(argv)
