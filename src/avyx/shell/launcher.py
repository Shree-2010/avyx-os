"""Left launcher panel: search, categories (Applications / Places / System / Settings / About) and power actions."""
import os
import platform

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402

from .. import apps, config, glass, sysinfo  # noqa: E402
from ..gfx import Glyph  # noqa: E402
from .util import BOTTOM, KB, LAYER, LEFT, layer_window, set_origin  # noqa: E402

px = config.px

CATS = [("apps", "Applications", "grid"), ("places", "Places", "folder"), ("system", "System", "activity"),
        ("settings", "Settings", "gear"), ("about", "About AVYX OS", "info")]
PLACES = [("Home", "folder-home", "path:~"), ("Desktop", "folder", "path:~/Desktop"), ("Documents", "folder-documents", "path:~/Documents"),
          ("Downloads", "folder-downloads", "path:~/Downloads"), ("Pictures", "folder-pictures", "path:~/Pictures"),
          ("Music", "folder-music", "path:~/Music"), ("Videos", "folder-videos", "path:~/Videos"), ("Recycle Bin", "trash", "path:trash:///")]
SYSTEM = [("Terminal", "avyx-terminal", "open:terminal"), ("Task Manager", "avyx-settings", "cmd:foot -e top"),
          ("Take Screenshot", "avyx-screenshot", "open:screenshot"), ("Install AVYX OS", "avyx-launcher", "installer")]
SETTINGS = [("Wi-Fi & Network", "avyx-settings", "settings:network"), ("Display", "avyx-settings", "settings:display"),
            ("Sound", "avyx-settings", "settings:sound"), ("Appearance", "avyx-settings", "settings:appearance"),
            ("Power & Battery", "avyx-settings", "settings:power"), ("Keyboard & Mouse", "avyx-settings", "settings:input")]


def _kernel():
    return platform.release()


def _cpu_model():
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.machine()


class Launcher:
    def __init__(self, shell):
        self.shell = shell
        self.cat = "apps"
        self.armed = False
        self.was_active = False
        self.dock_clear = px(10) + px(78) + px(14)
        self.win = layer_window(shell.app, "avyx-launcher", LAYER.TOP, anchors=(BOTTOM, LEFT),
                                margins={BOTTOM: self.dock_clear, LEFT: px(16)}, exclusive=-1, keyboard=KB.ON_DEMAND)
        self.W, self.H = px(470), px(560)
        set_origin(self.win, px(16), config.Screen.h - self.dock_clear - self.H)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(14))
        outer.set_size_request(self.W, self.H)
        for m in ("start", "end", "top", "bottom"):
            getattr(outer, "set_margin_" + m)(px(16))

        # search
        sf = Gtk.Box(spacing=px(10))
        sf.add_css_class("search-field")
        sf.append(Glyph("search", px(20)))
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Search apps...")
        self.entry.set_hexpand(True)
        self.entry.set_has_frame(False)
        self.entry.connect("changed", self._changed)
        self.entry.connect("activate", self._activate)
        sf.append(self.entry)
        kbd = Gtk.Label(label="Super K")
        kbd.add_css_class("kbd")
        sf.append(kbd)
        outer.append(sf)

        body = Gtk.Box(spacing=px(12), vexpand=True)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(5))
        left.set_size_request(px(190), -1)
        self.cat_btns = {}
        for cid, name, glyph in CATS:
            b = self._cat_button(name, glyph, chevron=cid != "about")
            b.connect("clicked", lambda _b, c=cid: self.select(c))
            self.cat_btns[cid] = b
            left.append(b)
        spacer = Gtk.Box(vexpand=True)
        left.append(spacer)
        for name, glyph, cmd, danger in (("Lock Screen", "lock", "lock", False), ("Log Out", "logout", "logout", False),
                                         ("Shut Down", "power", "poweroff", True)):
            b = self._cat_button(name, glyph, chevron=False)
            if danger:
                b.add_css_class("danger")
            b.connect("clicked", lambda _b, c=cmd: self._run(c))
            left.append(b)
        body.append(left)
        vl = Gtk.Box()
        vl.add_css_class("vline")
        body.append(vl)
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_hexpand(True)
        self.scroll.set_vexpand(True)
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_min_content_width(px(250))
        self.scroll.set_propagate_natural_width(False)
        self.list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(2))
        self.scroll.set_child(self.list)
        body.append(self.scroll)
        outer.append(body)

        self.win.set_child(glass.glass_box(outer, radius=px(30), tint=(0.075, 0.06, 0.11, 0.62)))
        self.win.connect("notify::is-active", self._active_changed)
        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self._key)
        self.win.add_controller(key)
        self.extra = None
        self.select("apps")

    # ------------------------------------------------------------------ widgets
    def _cat_button(self, text, glyph, chevron):
        b = Gtk.Button()
        b.add_css_class("cat")
        row = Gtk.Box(spacing=px(11))
        g = Glyph(glyph, px(20))
        g.add_css_class("glyph")
        row.append(g)
        lab = Gtk.Label(label=text, xalign=0, hexpand=True)
        row.append(lab)
        if chevron:
            c = Glyph("chev-r", px(14))
            c.add_css_class("dim")
            row.append(c)
        b.set_child(row)
        return b

    def _row(self, name, icon_widget, cmd=None, app=None, chevron=False):
        b = Gtk.Button()
        b.add_css_class("row")
        row = Gtk.Box(spacing=px(14))
        row.append(icon_widget)
        lab = Gtk.Label(label=name, xalign=0, hexpand=True)
        lab.set_ellipsize(3)
        row.append(lab)
        if chevron:
            c = Glyph("chev-r", px(14))
            c.add_css_class("dim")
            row.append(c)
        b.set_child(row)
        if app is not None:
            b.connect("clicked", lambda _b, a=app: self._launch_app(a))
        else:
            b.connect("clicked", lambda _b, c=cmd: self._run(c))
        return b

    def _clear(self):
        c = self.list.get_first_child()
        while c is not None:
            n = c.get_next_sibling()
            self.list.remove(c)
            c = n

    # ------------------------------------------------------------------ content
    def select(self, cid):
        self.cat = cid
        for k, b in self.cat_btns.items():
            (b.add_css_class if k == cid else b.remove_css_class)("sel")
        self.entry.set_text("") if self.entry.get_text() else None
        self._fill()

    def _all_apps(self):
        if self.extra is None:
            self.extra = apps.installed_extra()
        return list(apps.BUILTIN) + self.extra

    def _fill(self):
        self._clear()
        q = self.entry.get_text().strip().lower()
        sz = px(32)
        if q:
            hits = [a for a in self._all_apps() if q in a.name.lower() or q in a.keywords.lower() or q in a.generic.lower()]
            self.hits = hits
            for a in hits[:40]:
                self.list.append(self._row(a.name, apps.app_icon_widget(a, sz), app=a))
            if not hits:
                lab = Gtk.Label(label="No matching apps", xalign=0)
                lab.add_css_class("dim")
                lab.set_margin_start(px(12))
                lab.set_margin_top(px(10))
                self.list.append(lab)
            return
        self.hits = []
        if self.cat == "apps":
            order = ["browser", "files", "terminal", "settings", "videos", "music", "photos", "calculator", "editor", "store", "screenshot"]
            for i in order:
                a = apps.BY_ID[i]
                self.list.append(self._row(a.name, apps.app_icon_widget(a, sz), app=a, chevron=i in ("browser", "files", "terminal", "settings", "calculator")))
            for a in self.extra if self.extra is not None else self._all_apps()[len(apps.BUILTIN):]:
                self.list.append(self._row(a.name, apps.app_icon_widget(a, sz), app=a))
        elif self.cat == "places":
            for name, icon, cmd in PLACES:
                self.list.append(self._row(name, apps.icon_widget(icon, sz), cmd))
        elif self.cat == "system":
            for name, icon, cmd in SYSTEM:
                if cmd == "installer" and not (os.path.exists("/run/avyx/live") or config.TEST):
                    continue
                self.list.append(self._row(name, apps.icon_widget(icon, sz), cmd))
        elif self.cat == "settings":
            for name, icon, cmd in SETTINGS:
                self.list.append(self._row(name, apps.icon_widget(icon, sz), cmd))
        elif self.cat == "about":
            self.list.append(self._about())

    def _about(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(6), halign=Gtk.Align.CENTER)
        box.set_margin_top(px(22))
        box.append(apps.icon_widget("avyx-mark", px(84)))
        t = Gtk.Label(label="AVYX OS")
        t.add_css_class("big-quote")
        t.set_margin_top(px(8))
        box.append(t)
        s = Gtk.Label(label="BUILD BEYOND LIMITS")
        s.add_css_class("dim")
        box.append(s)
        ver = "0.1.0"
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("VERSION_ID="):
                        ver = line.split("=", 1)[1].strip().strip('"')
        except OSError:
            pass
        mem = sysinfo.mem_percent()[1]
        for label, val in (("Version", ver), ("Kernel", _kernel()), ("Processor", _cpu_model()), ("Memory", sysinfo.human(mem))):
            r = Gtk.Box(spacing=px(10), halign=Gtk.Align.CENTER)
            r.set_margin_top(px(4))
            a = Gtk.Label(label=label)
            a.add_css_class("dim")
            b = Gtk.Label(label=val)
            b.set_max_width_chars(28)
            b.set_ellipsize(3)
            r.append(a)
            r.append(b)
            box.append(r)
        return box

    # ------------------------------------------------------------------ behaviour
    def _changed(self, entry):
        self._fill()

    def _activate(self, entry):
        if getattr(self, "hits", None):
            self._launch_app(self.hits[0])

    def _launch_app(self, app):
        self.hide()
        self.shell.launch(app)

    def _run(self, cmd):
        self.hide()
        self.shell.invoke(cmd)

    def _key(self, ctl, keyval, keycode, state):
        from gi.repository import Gdk
        if keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False

    def _active_changed(self, win, _p):
        if win.is_active():
            self.was_active = True
        elif self.was_active and self.armed:
            self.hide()

    def visible(self):
        return self.win.get_visible()

    def show(self):
        self.was_active = False
        self.armed = False
        self.entry.set_text("")
        self.select("apps")
        self.win.present()
        self.entry.grab_focus()
        GLib.timeout_add(600, self._arm)

    def _arm(self):
        self.armed = True
        return False

    def hide(self):
        self.win.set_visible(False)
        self.armed = False

    def toggle(self):
        self.hide() if self.visible() else self.show()
