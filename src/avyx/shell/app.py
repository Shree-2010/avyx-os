"""AVYX shell (bootstrap version): wallpaper, top bar, readiness marker."""
import glob
import os
import sys
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402
from gi.repository import Gtk4LayerShell as LS  # noqa: E402

DATA = os.environ.get("AVYX_DATA", "/usr/share/avyx")


def wallpaper_path():
    files = sorted(glob.glob(os.path.join(DATA, "wallpapers", "*.jpg")))
    return files[0] if files else None


class Shell(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.avyx.Shell")
        self.ready_written = False

    def do_activate(self):
        css = Gtk.CssProvider()
        css.load_from_string(
            "window.bar { background: rgba(20,16,36,0.72); color: #f4efff; font-family: Inter; font-weight: 600; }"
            "window.bar label { padding: 0 12px; }"
        )
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        bg = Gtk.Window(application=self)
        LS.init_for_window(bg)
        LS.set_layer(bg, LS.Layer.BACKGROUND)
        for e in (LS.Edge.TOP, LS.Edge.BOTTOM, LS.Edge.LEFT, LS.Edge.RIGHT):
            LS.set_anchor(bg, e, True)
        LS.set_exclusive_zone(bg, -1)
        wp = wallpaper_path()
        pic = Gtk.Picture.new_for_filename(wp) if wp else Gtk.Picture()
        pic.set_content_fit(Gtk.ContentFit.COVER)
        bg.set_child(pic)
        bg.present()

        bar = Gtk.Window(application=self)
        bar.add_css_class("bar")
        LS.init_for_window(bar)
        LS.set_layer(bar, LS.Layer.TOP)
        for e in (LS.Edge.TOP, LS.Edge.LEFT, LS.Edge.RIGHT):
            LS.set_anchor(bar, e, True)
        LS.auto_exclusive_zone_enable(bar)
        box = Gtk.CenterBox()
        box.set_start_widget(Gtk.Label(label="AVYX OS"))
        self.clock = Gtk.Label()
        box.set_end_widget(self.clock)
        bar.set_child(box)
        bar.set_default_size(-1, 30)
        bar.connect("map", self.on_bar_mapped)
        bar.present()
        self.tick()
        GLib.timeout_add_seconds(1, self.tick)

    def tick(self):
        self.clock.set_label(time.strftime("%a %b %d  %I:%M %p"))
        return True

    def on_bar_mapped(self, *_):
        GLib.timeout_add(1500, self.write_ready)

    def write_ready(self):
        if not self.ready_written:
            self.ready_written = True
            try:
                with open("/run/avyx/shell-ready", "w") as f:
                    f.write("bootstrap-shell")
            except OSError as e:
                print("cannot write ready marker:", e, file=sys.stderr)
            os.system("avyx-mark shell_mapped")
        return False


def main(argv):
    return Shell().run(argv)
