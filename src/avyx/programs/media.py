"""avyx-media: pick files (or take them from the command line) and play them with mpv."""
import os
import shutil
import sys

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib, Gtk  # noqa: E402

from .. import appkit, config  # noqa: E402

MPV = ["mpv", "--force-window=yes", "--keep-open=no", "--hwdec=auto-safe", "--gpu-context=wayland", "--osc=yes", "--title=${media-title} — AVYX Media"]


def play(files, audio):
    cmd = list(MPV)
    if audio:
        cmd += ["--force-window=yes", "--audio-display=embedded-first"]
    os.execvp("mpv", cmd + files)


class MediaApp(Gtk.Application):
    def __init__(self, files, audio):
        super().__init__(application_id="org.avyx.Media")
        self.files, self.audio = files, audio

    def do_startup(self):
        Gtk.Application.do_startup(self)
        appkit.setup_env()

    def do_activate(self):
        self.hold()
        dlg = Gtk.FileDialog()
        dlg.set_title("Choose %s to play" % ("music" if self.audio else "videos"))
        home = os.path.expanduser("~")
        start = os.path.join(home, "Music" if self.audio else "Videos")
        dlg.set_initial_folder(Gio.File.new_for_path(start if os.path.isdir(start) else home))
        flt = Gtk.FileFilter()
        flt.set_name("Audio" if self.audio else "Video and audio")
        flt.add_mime_type("audio/*")
        if not self.audio:
            flt.add_mime_type("video/*")
        lst = Gio.ListStore.new(Gtk.FileFilter)
        lst.append(flt)
        dlg.set_filters(lst)

        def done(d, res):
            try:
                files = [f.get_path() for f in d.open_multiple_finish(res)]
            except GLib.Error:
                self.quit()
                return
            if files:
                play(files, self.audio)
            self.quit()
        dlg.open_multiple(None, None, done)


def main(argv):
    args = argv[1:]
    audio = "--audio" in args
    files = [a for a in args if not a.startswith("--")]
    if not shutil.which("mpv"):
        config.spawn(["avyx-ctl", "toast:No media player is installed in this build yet"])
        return 1
    if files:
        play(files, audio)
    return MediaApp(files, audio).run(argv[:1])
