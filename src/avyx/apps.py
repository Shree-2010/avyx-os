"""Application catalogue (built-in AVYX apps + installed .desktop apps), icons and process tracking."""
import os
import shutil
import subprocess

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk  # noqa: E402

from . import config  # noqa: E402


class App:
    def __init__(self, id, name, icon, argv, generic=None, keywords=""):
        self.id = id
        self.name = name
        self.icon = icon            # AVYX icon name, or None when `gicon` is used
        self.argv = argv
        self.gicon = None
        self.generic = generic or ""
        self.keywords = keywords
        self.proc = None

    def available(self):
        return bool(self.argv) and (shutil.which(self.argv[0]) is not None)

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def launch(self, extra=None):
        argv = list(self.argv) + list(extra or [])
        p = config.spawn(argv)
        if p is not None:
            self.proc = p
        return p is not None


BUILTIN = [
    App("browser", "Web Browser", "avyx-browser", ["avyx-browser"], "Internet", "brave chrome firefox internet web"),
    App("files", "Files", "avyx-files", ["avyx-files"], "File Manager", "folder explorer finder"),
    App("terminal", "Terminal", "avyx-terminal", ["foot"], "Command Line", "console shell bash cli"),
    App("settings", "Settings", "avyx-settings", ["avyx-settings"], "Preferences", "preferences configuration wifi display"),
    App("videos", "Videos", "avyx-video", ["avyx-media"], "Media Player", "movie player mpv film"),
    App("music", "Music", "avyx-music", ["avyx-media", "--audio"], "Audio Player", "songs audio player"),
    App("photos", "Photos", "avyx-photos", ["avyx-photos"], "Image Viewer", "pictures images viewer"),
    App("calculator", "Calculator", "avyx-calculator", ["avyx-calculator"], "Calculator", "math"),
    App("editor", "Text Editor", "avyx-editor", ["avyx-editor"], "Text Editor", "notes write code"),
    App("store", "AVYX Store", "avyx-store", ["avyx-store"], "Software", "install apps wine android"),
    App("screenshot", "Screenshot", "avyx-screenshot", ["avyx-screenshot"], "Screenshot", "capture screen"),
]
BY_ID = {a.id: a for a in BUILTIN}

# the order used by the launcher's application list and the dock
DOCK_IDS = ["launcher", "files", "store", "browser", "terminal", "settings", "photos", "videos", "music", "editor", "|", "trash"]


def installed_extra():
    """Other desktop applications found on the system (excluding our own entries)."""
    out = []
    seen = {a.argv[0] for a in BUILTIN}
    try:
        infos = Gio.AppInfo.get_all()
    except Exception:
        infos = []
    for ai in infos:
        try:
            if not ai.should_show():
                continue
            exe = ai.get_executable() or ""
            if os.path.basename(exe) in seen:
                continue
            a = App("x:" + (ai.get_id() or exe), ai.get_display_name(), None, [], "", (ai.get_keywords() or [""])[0] if hasattr(ai, "get_keywords") else "")
            a.gicon = ai.get_icon()
            a.appinfo = ai
            out.append(a)
        except Exception:
            continue
    out.sort(key=lambda a: a.name.lower())
    return out


def launch_extra(app):
    try:
        app.appinfo.launch([], None)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------------------------- icons
_pb = {}
_tex = {}


def pixbuf(name, size):
    key = (name, size)
    if key not in _pb:
        path = config.icon_path(name)
        try:
            _pb[key] = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, True)
        except GLib.Error:
            _pb[key] = None
    return _pb[key]


def texture(name, size):
    key = (name, size)
    if key not in _tex:
        pb = pixbuf(name, size)
        _tex[key] = Gdk.Texture.new_for_pixbuf(pb) if pb else None
    return _tex[key]


def icon_widget(name, size):
    t = texture(name, size * 2 if size < 96 else size)
    pic = Gtk.Picture.new_for_paintable(t) if t else Gtk.Picture()
    pic.set_size_request(size, size)
    pic.set_can_shrink(True)
    pic.set_content_fit(Gtk.ContentFit.CONTAIN)
    pic.set_halign(Gtk.Align.CENTER)
    pic.set_valign(Gtk.Align.CENTER)
    return pic


def app_icon_widget(app, size):
    if app.icon:
        return icon_widget(app.icon, size)
    img = Gtk.Image()
    if app.gicon is not None:
        img.set_from_gicon(app.gicon)
    else:
        img.set_from_icon_name("application-x-executable")
    img.set_pixel_size(size)
    return img
