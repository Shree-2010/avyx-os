"""AVYX Photos: a thumbnail library for ~/Pictures and a simple image viewer."""
import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk  # noqa: E402

from .. import appkit, apps, config  # noqa: E402
from ..appkit import AppWindow, icon_button  # noqa: E402

px = config.px
HOME = os.path.expanduser("~")
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff"}


def find_images(root, depth=2):
    out = []
    try:
        for dp, dn, fn in os.walk(root):
            if dp[len(root):].count(os.sep) >= depth:
                dn[:] = []
            dn[:] = [d for d in dn if not d.startswith(".")]
            for f in sorted(fn):
                if os.path.splitext(f)[1].lower() in IMG_EXT:
                    out.append(os.path.join(dp, f))
            if len(out) > 1500:
                break
    except OSError:
        pass
    return sorted(out)


class PhotosWindow(AppWindow):
    def __init__(self, app, path=None):
        super().__init__(app, "Photos", 980, 640)
        self.images = []
        self.index = -1
        self.zoom = None          # None = fit
        self.back_b = icon_button("chev-l", "Library (Esc)", self.show_library)
        self.header_append(self.back_b)
        self.prev_b = icon_button("prev", "Previous (Left)", lambda: self.step(-1))
        self.next_b = icon_button("next", "Next (Right)", lambda: self.step(1))
        self.header_append(self.prev_b)
        self.header_append(self.next_b)
        self.title_l = Gtk.Label(label="Photos", xalign=0, hexpand=True)
        self.title_l.add_css_class("app-title")
        self.title_l.set_margin_start(px(8))
        self.header_append(self.title_l)
        self.header_append(icon_button("plus", "Zoom in (+)", lambda: self.set_zoom(1.25)))
        self.header_append(icon_button("grid", "Fit to window (F)", lambda: self.set_zoom(None)))
        self.header_append(icon_button("folder", "Open…", self.open_dialog))

        self.stack = Gtk.Stack()
        self.stack.set_vexpand(True)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.body.append(self.stack)
        # library
        self.lib_scroll = Gtk.ScrolledWindow()
        self.stack.add_named(self.lib_scroll, "lib")
        # viewer
        self.pic = Gtk.Picture()
        self.pic.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.pic.set_can_shrink(True)
        self.vscroll = Gtk.ScrolledWindow()
        self.vscroll.add_css_class("photo-bg")
        self.vscroll.set_child(self.pic)
        self.stack.add_named(self.vscroll, "view")
        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self._key)
        self.add_controller(key)
        self._thumbs = []
        if path and os.path.isfile(path):
            d = os.path.dirname(os.path.abspath(path))
            self.images = find_images(d, 0) or [path]
            self.show_image(self.images.index(os.path.abspath(path)) if os.path.abspath(path) in self.images else 0)
        else:
            self.images = find_images(os.path.join(HOME, "Pictures"))
            self.show_library()

    # ---------------------------------------------------------------- library
    def show_library(self):
        self.stack.set_visible_child_name("lib")
        self.back_b.set_visible(False)
        self.prev_b.set_visible(False)
        self.next_b.set_visible(False)
        self.title_l.set_label("Photos")
        if not self.images:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(10), valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER)
            box.append(apps.icon_widget("avyx-photos", px(96)))
            t = Gtk.Label(label="No photos yet")
            t.add_css_class("dlg-title")
            box.append(t)
            s = Gtk.Label(label="Put pictures in your Pictures folder, or open one.")
            s.add_css_class("dim-label")
            box.append(s)
            b = Gtk.Button(label="Open a picture…")
            b.add_css_class("btn")
            b.add_css_class("primary")
            b.connect("clicked", lambda *_: self.open_dialog())
            b.set_halign(Gtk.Align.CENTER)
            box.append(b)
            self.lib_scroll.set_child(box)
            return
        fb = Gtk.FlowBox()
        fb.add_css_class("items")
        fb.set_valign(Gtk.Align.START)
        fb.set_selection_mode(Gtk.SelectionMode.NONE)
        fb.set_homogeneous(True)
        fb.set_max_children_per_line(30)
        fb.set_row_spacing(px(8))
        fb.set_column_spacing(px(8))
        self._thumbs = []
        for i, p in enumerate(self.images):
            pic = Gtk.Picture()
            pic.set_size_request(px(150), px(110))
            pic.set_content_fit(Gtk.ContentFit.COVER)
            pic.set_can_shrink(True)
            pic.set_overflow(Gtk.Overflow.HIDDEN)
            pic.add_css_class("art")
            b = Gtk.Button()
            b.add_css_class("avx")
            b.set_child(pic)
            b.connect("clicked", lambda _b, ii=i: self.show_image(ii))
            fb.append(b)
            self._thumbs.append((p, pic))
        self.lib_scroll.set_child(fb)
        GLib.idle_add(self._thumb_step)

    def _thumb_step(self):
        for _ in range(4):
            if not self._thumbs:
                return False
            p, pic = self._thumbs.pop(0)
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(p, px(300), px(220), True)
                pic.set_paintable(Gdk.Texture.new_for_pixbuf(pb))
            except GLib.Error:
                pass
        return True

    # ---------------------------------------------------------------- viewer
    def show_image(self, i):
        if not self.images:
            return
        self.index = i % len(self.images)
        p = self.images[self.index]
        try:
            self.texture = Gdk.Texture.new_from_filename(p)
        except GLib.Error as ex:
            appkit.message(self, "Could not open image", ex.message)
            return
        self.pic.set_paintable(self.texture)
        self.zoom = None
        self._apply_zoom()
        self.stack.set_visible_child_name("view")
        self.back_b.set_visible(True)
        multi = len(self.images) > 1
        self.prev_b.set_visible(multi)
        self.next_b.set_visible(multi)
        self.title_l.set_label("%s   (%d/%d)" % (os.path.basename(p), self.index + 1, len(self.images)))
        self.set_title(os.path.basename(p) + " — Photos")

    def step(self, d):
        if self.images:
            self.show_image(self.index + d)

    def set_zoom(self, factor):
        if self.stack.get_visible_child_name() != "view":
            return
        if factor is None:
            self.zoom = None
        else:
            cur = self.zoom or max(0.05, min(self.vscroll.get_width() / max(1, self.texture.get_width()), self.vscroll.get_height() / max(1, self.texture.get_height())))
            self.zoom = max(0.05, min(8.0, cur * factor))
        self._apply_zoom()

    def _apply_zoom(self):
        if self.zoom is None:
            self.pic.set_can_shrink(True)
            self.pic.set_size_request(-1, -1)
            self.pic.set_halign(Gtk.Align.FILL)
            self.pic.set_valign(Gtk.Align.FILL)
        else:
            self.pic.set_can_shrink(False)
            self.pic.set_size_request(int(self.texture.get_width() * self.zoom), int(self.texture.get_height() * self.zoom))
            self.pic.set_halign(Gtk.Align.CENTER)
            self.pic.set_valign(Gtk.Align.CENTER)

    def open_dialog(self):
        dlg = Gtk.FileDialog()

        def done(d, res):
            try:
                f = d.open_finish(res)
            except GLib.Error:
                return
            path = os.path.abspath(f.get_path())
            self.images = find_images(os.path.dirname(path), 0) or [path]
            self.show_image(self.images.index(path) if path in self.images else 0)
        dlg.open(self, None, done)

    def _key(self, ctl, keyval, keycode, state):
        if keyval == Gdk.KEY_Left:
            self.step(-1)
        elif keyval == Gdk.KEY_Right:
            self.step(1)
        elif keyval == Gdk.KEY_Escape:
            self.show_library()
        elif keyval in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
            self.set_zoom(1.25)
        elif keyval in (Gdk.KEY_minus, Gdk.KEY_KP_Subtract):
            self.set_zoom(0.8)
        elif keyval in (Gdk.KEY_f, Gdk.KEY_F, Gdk.KEY_0):
            self.set_zoom(None)
        else:
            return False
        return True


class PhotosApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.avyx.Photos", flags=Gio.ApplicationFlags.HANDLES_OPEN)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        appkit.setup_env()

    def do_activate(self):
        PhotosWindow(self).present()

    def do_open(self, files, n, hint):
        for f in files:
            PhotosWindow(self, f.get_path()).present()


def main(argv):
    args = [argv[0]] + [Gio.File.new_for_commandline_arg(a).get_uri() for a in argv[1:]]
    return PhotosApp().run(args)
