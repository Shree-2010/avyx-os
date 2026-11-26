"""AVYX Screenshot: a three-button window, or `avyx-screenshot --full|--area` for shortcuts."""
import os
import shutil
import subprocess
import sys
import time

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402

from .. import appkit, config  # noqa: E402
from ..appkit import AppWindow  # noqa: E402

px = config.px
OUTDIR = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")


def capture(mode):
    """Take the screenshot synchronously; returns the saved path or None."""
    if not shutil.which("grim"):
        return None
    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, time.strftime("AVYX Screenshot %Y-%m-%d %H.%M.%S.png"))
    cmd = ["grim"]
    if mode == "area":
        try:
            geo = subprocess.run(["slurp"], capture_output=True, text=True, timeout=120).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            geo = ""
        if not geo:
            return None
        cmd += ["-g", geo]
    cmd.append(path)
    if subprocess.run(cmd).returncode != 0:
        return None
    if shutil.which("wl-copy"):
        try:
            with open(path, "rb") as f:
                subprocess.run(["wl-copy", "--type", "image/png"], stdin=f, timeout=5)
        except (OSError, subprocess.SubprocessError):
            pass
    config.spawn(["avyx-ctl", "toast:Screenshot saved to Pictures/Screenshots"])
    return path


class ShotWindow(AppWindow):
    def __init__(self, app):
        super().__init__(app, "Screenshot", 420, 200)
        self.set_resizable(False)
        t = Gtk.Label(label="Screenshot", xalign=0, hexpand=True)
        t.add_css_class("app-title")
        self.header_append(t)
        box = Gtk.Box(spacing=px(12), homogeneous=True)
        for m in ("start", "end", "top", "bottom"):
            getattr(box, "set_margin_" + m)(px(20))
        for text, mode, delay in (("Entire Screen", "full", 0), ("Selection", "area", 0), ("In 5 Seconds", "full", 5)):
            b = Gtk.Button(label=text)
            b.add_css_class("btn")
            b.set_size_request(-1, px(70))
            b.connect("clicked", lambda _b, m=mode, d=delay: self.go(m, d))
            box.append(b)
        self.body.append(box)
        note = Gtk.Label(label="Shortcuts: Print = entire screen, Super+Shift+S = selection")
        note.add_css_class("dim-label")
        self.body.append(note)

    def go(self, mode, delay):
        self.set_visible(False)

        def run():
            capture(mode)
            self.get_application().quit()
            return False
        GLib.timeout_add(int((delay or 0.5) * 1000) if delay else 500, run)


class ShotApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.avyx.Screenshot")

    def do_startup(self):
        Gtk.Application.do_startup(self)
        appkit.setup_env()

    def do_activate(self):
        ShotWindow(self).present()


def main(argv):
    if len(argv) > 1 and argv[1] in ("--full", "--area"):
        return 0 if capture(argv[1][2:]) else 1
    return ShotApp().run(argv[:1])
