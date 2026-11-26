"""Global top menu bar: brand, application menu, status icons, clock."""
import threading
import time

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402

from .. import apps, config, sysinfo  # noqa: E402
from ..gfx import Glyph  # noqa: E402
from .util import KB, LAYER, LEFT, RIGHT, TOP, Menu, layer_window  # noqa: E402

px = config.px

MENUS = {
    "File": [("New Window", "files:new", "Ctrl+N"), ("New Folder", "files:newfolder", "Ctrl+Shift+N"), "-",
             ("Open Home Folder", "path:~", None), ("Open Terminal Here", "open:terminal", None), "-",
             ("Close Window", "window:close", "Ctrl+W")],
    "Edit": [("Undo", None, "Ctrl+Z"), ("Redo", None, "Ctrl+Shift+Z"), "-", ("Cut", None, "Ctrl+X"), ("Copy", None, "Ctrl+C"),
             ("Paste", None, "Ctrl+V"), ("Select All", None, "Ctrl+A")],
    "View": [("As Icons", "files:view-icons", None), ("As List", "files:view-list", None), "-",
             ("Show Hidden Files", "files:hidden", "Ctrl+H"), "-", ("Overview", "overview", "Super+Tab")],
    "Go": [("Home", "path:~", None), ("Desktop", "path:~/Desktop", None), ("Documents", "path:~/Documents", None),
           ("Downloads", "path:~/Downloads", None), ("Pictures", "path:~/Pictures", None), ("Music", "path:~/Music", None),
           ("Videos", "path:~/Videos", None), "-", ("Trash", "path:trash:///", None)],
    "Window": [("Minimize", "window:minimize", None), ("Maximize", "window:maximize", None), ("Close", "window:close", "Ctrl+W"),
               "-", ("Overview", "overview", "Super+Tab")],
    "Help": [("Search", "spotlight", "Super+Space"), ("Keyboard Shortcuts", "shortcuts", None), "-", ("About AVYX OS", "about", None)],
}


class TopBar:
    def __init__(self, shell):
        self.shell = shell
        self.win = layer_window(shell.app, "avyx-topbar", LAYER.TOP, anchors=(TOP, LEFT, RIGHT), exclusive="auto", keyboard=KB.NONE)
        self.win.set_default_size(-1, px(30))
        bar = Gtk.CenterBox()
        bar.add_css_class("topbar")
        bar.set_size_request(-1, px(30))
        self.win.set_child(bar)

        # ---- left: brand + menus
        left = Gtk.Box(valign=Gtk.Align.CENTER)
        left.set_margin_start(px(14))
        left.append(apps.icon_widget("avyx-mark", px(18)))
        brand = Gtk.Label(label="AVYX OS")
        brand.add_css_class("brand-text")
        brand.set_margin_start(px(9))
        left.append(brand)
        sep = Gtk.Box()
        sep.add_css_class("brand-sep")
        left.append(sep)
        self.app_btn = self._menu_button("Files", None, app=True)
        left.append(self.app_btn)
        for name, items in MENUS.items():
            left.append(self._menu_button(name, items))
        bar.set_start_widget(left)

        # ---- right: status
        right = Gtk.Box(valign=Gtk.Align.CENTER, spacing=px(2))
        right.set_margin_end(px(12))
        self.net = Glyph("wifi", px(17))
        self.bt = Glyph("bluetooth", px(16))
        self.vol = Glyph("volume", px(17))
        self.bat_glyph = Glyph("battery", px(21), 0.87)
        self.bat_label = Gtk.Label(label="87%")
        self.bat_label.set_margin_start(px(2))
        for g in (self.net, self.bt, self.vol):
            right.append(self._status_btn(g, lambda *_: shell.invoke("cc")))
        bat_box = Gtk.Box(spacing=px(4))
        bat_box.append(self.bat_glyph)
        bat_box.append(self.bat_label)
        self.bat_btn = self._status_btn(bat_box, lambda *_: shell.invoke("cc"))
        right.append(self.bat_btn)
        self.clock = Gtk.Label()
        self.clock.set_margin_start(px(8))
        self.clock.set_margin_end(px(8))
        right.append(self._status_btn(self.clock, lambda *_: shell.invoke("cc")))
        dot = Gtk.Box()
        dot.add_css_class("dot-accent")
        dot.set_valign(Gtk.Align.CENTER)
        right.append(self._status_btn(dot, lambda *_: shell.invoke("cc")))
        bar.set_end_widget(right)

        self.win.connect("map", lambda *_: shell.on_bar_mapped())
        self._last_clock = None
        self.tick()
        GLib.timeout_add(1000, self.tick)
        self.refresh_status()
        GLib.timeout_add_seconds(5, self.refresh_status)
        self.win.present()

    # ------------------------------------------------------------------ building blocks
    def _menu_button(self, text, items, app=False):
        b = Gtk.Button()
        b.add_css_class("avx")
        b.add_css_class("menu")
        if app:
            b.add_css_class("app")
        b.set_child(Gtk.Label(label=text))
        if items:
            m = Menu(self.shell, b, items)
            b.connect("clicked", lambda *_: m.popup())
            m.pop.connect("notify::visible", lambda p, _x, bb=b: bb.add_css_class("open") if p.get_visible() else bb.remove_css_class("open"))
        else:
            b.connect("clicked", lambda *_: self.shell.invoke("spotlight"))
        return b

    def _status_btn(self, child, cb):
        b = Gtk.Button()
        b.add_css_class("avx")
        b.add_css_class("status")
        b.set_child(child)
        b.connect("clicked", cb)
        return b

    # ------------------------------------------------------------------ state
    def set_app_name(self, name):
        self.app_btn.get_child().set_label(name)

    def tick(self):
        t = time.strftime("%a, %b %-d   %-I:%M %p") if not config.settings.get("clock24") else time.strftime("%a, %b %-d   %H:%M")
        if t != self._last_clock:
            self._last_clock = t
            self.clock.set_label(t)
        return True

    def refresh_status(self):
        kind = sysinfo.network_kind()
        self.net.set_glyph({"wifi": "wifi", "ethernet": "ethernet"}.get(kind, "wifi-off"))
        self.bt.set_visible(sysinfo.has_bluetooth_hw() or config.TEST)
        b = sysinfo.battery()
        if config.TEST:
            b = (87, False)
        if b is None:
            self.bat_btn.set_visible(False)
        else:
            self.bat_btn.set_visible(True)
            self.bat_glyph.set_value(b[0] / 100.0)
            self.bat_label.set_label("%d%%" % b[0])

        def work():
            v = sysinfo.volume()
            if v:
                GLib.idle_add(lambda: self.vol.set_glyph("volume-mute" if (v[1] or v[0] <= 0.001) else "volume"))
        threading.Thread(target=work, daemon=True).start()
        return True
