"""Shared pieces for AVYX apps: environment setup, a window with traffic-light controls, small dialogs."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

from . import config, theme  # noqa: E402
from .gfx import Glyph  # noqa: E402

px = config.px


def setup_env():
    """Call from do_startup of every app: scale factor, CSS, decoration layout."""
    config.Screen.init()
    theme.apply()
    s = Gtk.Settings.get_default()
    try:
        s.set_property("gtk-decoration-layout", "close,minimize,maximize:")
        s.set_property("gtk-application-prefer-dark-theme", True)
        s.set_property("gtk-font-name", "Inter 10")
    except Exception:
        pass


class AppWindow(Gtk.ApplicationWindow):
    """Top-level window: glass-dark body, our own title bar (draggable) with traffic-light controls."""

    def __init__(self, app, title, width=900, height=600):
        super().__init__(application=app, title=title)
        self.add_css_class("avyx-app")
        self.set_default_size(px(width), px(height))
        self.header = Gtk.Box(spacing=px(8))
        self.header.add_css_class("app-header")
        self.controls = Gtk.WindowControls.new(Gtk.PackType.START)
        self.header.append(self.controls)
        self.set_titlebar(Gtk.WindowHandle(child=self.header))
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.body)

    def header_append(self, w):
        self.header.append(w)
        return w


def icon_button(glyph, tooltip, cb, size=17):
    b = Gtk.Button()
    b.add_css_class("tool")
    b.set_child(Glyph(glyph, px(size)))
    b.set_tooltip_text(tooltip)
    b.connect("clicked", lambda *_: cb())
    return b


def message(parent, title, text):
    dlg = Gtk.AlertDialog()
    dlg.set_message(title)
    dlg.set_detail(text)
    dlg.set_buttons(["OK"])
    dlg.show(parent)


def confirm(parent, title, text, yes_label, cb):
    dlg = Gtk.AlertDialog()
    dlg.set_message(title)
    dlg.set_detail(text)
    dlg.set_buttons(["Cancel", yes_label])
    dlg.set_cancel_button(0)
    dlg.set_default_button(1)

    def done(d, res):
        try:
            if d.choose_finish(res) == 1:
                cb()
        except GLib.Error:
            pass
    dlg.choose(parent, None, done)


def prompt(parent, title, initial, ok_label, cb):
    """Modal single-line text prompt."""
    win = Gtk.Window(transient_for=parent, modal=True, title=title)
    win.add_css_class("avyx-app")
    win.add_css_class("dialog")
    win.set_default_size(px(380), -1)
    win.set_resizable(False)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(12))
    for m in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + m)(px(18))
    t = Gtk.Label(label=title, xalign=0)
    t.add_css_class("dlg-title")
    box.append(t)
    entry = Gtk.Entry()
    entry.set_text(initial or "")
    entry.add_css_class("field")
    box.append(entry)
    row = Gtk.Box(spacing=px(8), halign=Gtk.Align.END)
    cancel = Gtk.Button(label="Cancel")
    cancel.add_css_class("btn")
    ok = Gtk.Button(label=ok_label)
    ok.add_css_class("btn")
    ok.add_css_class("primary")
    row.append(cancel)
    row.append(ok)
    box.append(row)
    win.set_child(box)

    def accept(*_):
        text = entry.get_text().strip()
        win.close()
        if text:
            cb(text)
    cancel.connect("clicked", lambda *_: win.close())
    ok.connect("clicked", accept)
    entry.connect("activate", accept)
    win.present()
    entry.grab_focus()
    return win
