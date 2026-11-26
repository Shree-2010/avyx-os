"""AVYX Text Editor: plain text and code, open/save, unsaved-changes protection."""
import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402

from .. import appkit, config  # noqa: E402
from ..appkit import AppWindow, icon_button  # noqa: E402

px = config.px


class EditorWindow(AppWindow):
    def __init__(self, app, path=None):
        super().__init__(app, "Text Editor", 860, 600)
        self.path = None
        self.modified = False
        self.header_append(icon_button("plus", "New (Ctrl+N)", lambda: self.get_application().new_window()))
        self.header_append(icon_button("folder", "Open (Ctrl+O)", self.open_dialog))
        self.header_append(icon_button("download", "Save (Ctrl+S)", self.save))
        self.title_l = Gtk.Label(xalign=0, hexpand=True)
        self.title_l.add_css_class("app-title")
        self.title_l.set_margin_start(px(8))
        self.header_append(self.title_l)
        self.pos = Gtk.Label(label="Ln 1, Col 1")
        self.pos.add_css_class("dim-label")
        self.header_append(self.pos)
        self.view = Gtk.TextView()
        self.view.add_css_class("editor")
        self.view.set_monospace(True)
        self.view.set_left_margin(px(18))
        self.view.set_right_margin(px(18))
        self.view.set_top_margin(px(14))
        self.view.set_bottom_margin(px(14))
        self.view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.buf = self.view.get_buffer()
        self.buf.connect("changed", self._changed)
        self.buf.connect("notify::cursor-position", self._cursor)
        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.set_child(self.view)
        self.body.append(sc)
        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self._key)
        self.add_controller(key)
        self.connect("close-request", self._close_request)
        self._update_title()
        if path:
            self.load(path)

    # ---------------------------------------------------------------- state
    def _update_title(self):
        name = os.path.basename(self.path) if self.path else "Untitled"
        self.title_l.set_label(("• " if self.modified else "") + name)
        self.set_title(name + (" •" if self.modified else "") + " — Text Editor")

    def _changed(self, buf):
        if not self._loading:
            self.modified = True
            self._update_title()

    _loading = False

    def _cursor(self, buf, _p):
        it = buf.get_iter_at_offset(buf.get_property("cursor-position"))
        self.pos.set_label("Ln %d, Col %d" % (it.get_line() + 1, it.get_line_offset() + 1))

    # ---------------------------------------------------------------- file ops
    def load(self, path):
        try:
            with open(path, "rb") as f:
                data = f.read(8 * 1024 * 1024)
            text = data.decode("utf-8", errors="replace")
        except OSError as ex:
            appkit.message(self, "Could not open file", ex.strerror or str(ex))
            return
        self._loading = True
        self.buf.set_text(text)
        self._loading = False
        self.buf.place_cursor(self.buf.get_start_iter())
        self.path = path
        self.modified = False
        self._update_title()

    def open_dialog(self):
        dlg = Gtk.FileDialog()

        def done(d, res):
            try:
                f = d.open_finish(res)
            except GLib.Error:
                return
            if self.path is None and not self.modified:
                self.load(f.get_path())
            else:
                self.get_application().new_window(f.get_path())
        dlg.open(self, None, done)

    def save(self, then=None):
        if self.path:
            self._write(self.path, then)
            return
        dlg = Gtk.FileDialog()
        dlg.set_initial_name("untitled.txt")

        def done(d, res):
            try:
                f = d.save_finish(res)
            except GLib.Error:
                return
            self._write(f.get_path(), then)
        dlg.save(self, None, done)

    def _write(self, path, then=None):
        text = self.buf.get_text(self.buf.get_start_iter(), self.buf.get_end_iter(), False)
        try:
            tmp = path + ".avyx-tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, path)
        except OSError as ex:
            appkit.message(self, "Could not save", ex.strerror or str(ex))
            return
        self.path = path
        self.modified = False
        self._update_title()
        if then:
            then()

    def _close_request(self, win):
        if not self.modified:
            return False
        dlg = Gtk.AlertDialog()
        dlg.set_message("Save changes before closing?")
        dlg.set_detail("Your changes will be lost if you don't save them.")
        dlg.set_buttons(["Cancel", "Discard", "Save"])
        dlg.set_cancel_button(0)
        dlg.set_default_button(2)

        def done(d, res):
            try:
                r = d.choose_finish(res)
            except GLib.Error:
                return
            if r == 1:
                self.modified = False
                self.close()
            elif r == 2:
                self.save(then=self.close)
        dlg.choose(self, None, done)
        return True

    def _key(self, ctl, keyval, keycode, state):
        if not state & Gdk.ModifierType.CONTROL_MASK:
            return False
        k = Gdk.keyval_name(keyval).lower()
        if k == "s":
            self.save()
        elif k == "o":
            self.open_dialog()
        elif k == "n":
            self.get_application().new_window()
        elif k == "w":
            self.close()
        else:
            return False
        return True


class EditorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.avyx.Editor", flags=Gio.ApplicationFlags.HANDLES_OPEN)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        appkit.setup_env()

    def new_window(self, path=None):
        EditorWindow(self, path).present()

    def do_activate(self):
        self.new_window()

    def do_open(self, files, n, hint):
        for f in files:
            self.new_window(f.get_path())


def main(argv):
    args = [argv[0]] + [Gio.File.new_for_commandline_arg(a).get_uri() for a in argv[1:]]
    return EditorApp().run(args)
