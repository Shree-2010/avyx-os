"""Paths, settings, screen geometry and the shared scale factor for the AVYX shell."""
import json
import os
import subprocess

DATA = os.environ.get("AVYX_DATA", "/usr/share/avyx")
TEST = bool(os.environ.get("AVYX_TEST"))
CFG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "avyx")
ACCENT = (1.0, 0.54, 0.12)            # AVYX orange
ACCENT_HEX = "#ff8a1f"


def icon_path(name):
    return os.path.join(DATA, "icons", name + ".png")


def wallpaper_path():
    custom = settings.get("wallpaper")
    if custom and os.path.exists(custom):
        return custom
    p = os.path.join(DATA, "wallpapers", "default.jpg")
    return p if os.path.exists(p) else None


def profile():
    """Graphics profile chosen by avyx-session: full | lite | basic."""
    p = os.environ.get("AVYX_GFX") or os.environ.get("AVYX_PROFILE")
    if not p:
        try:
            with open("/run/avyx/gfx-profile") as f:
                p = f.read().strip()
        except OSError:
            p = "full"
    return p if p in ("full", "lite", "basic") else "full"


class _Settings:
    DEFAULTS = {"location": None, "magnify": True, "wallpaper": None, "widgets": True, "clock24": False}

    def __init__(self):
        self.path = os.path.join(CFG_DIR, "shell.json")
        self.data = dict(self.DEFAULTS)
        try:
            with open(self.path) as f:
                self.data.update(json.load(f))
        except (OSError, ValueError):
            pass

    def get(self, k, default=None):
        return self.data.get(k, default)

    def set(self, k, v):
        self.data[k] = v
        try:
            os.makedirs(CFG_DIR, exist_ok=True)
            with open(self.path, "w") as f:
                json.dump(self.data, f, indent=1)
        except OSError:
            pass


settings = _Settings()


class Screen:
    """First monitor geometry and the UI scale derived from it (reference design is 1536x1024)."""
    w = 1536
    h = 1024
    S = 1.0

    @classmethod
    def init(cls):
        import gi
        gi.require_version("Gdk", "4.0")
        from gi.repository import Gdk
        d = Gdk.Display.get_default()
        mons = d.get_monitors()
        if mons.get_n_items():
            g = mons.get_item(0).get_geometry()
            cls.w, cls.h = g.width, g.height
        cls.S = max(0.78, min(1.35, min(cls.w / 1536.0, cls.h / 1024.0) * 1.04))
        return cls


def px(n):
    return max(1, int(round(n * Screen.S)))


def spawn(argv, **kw):
    """Start a program detached from the shell; returns the Popen or None."""
    try:
        return subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, start_new_session=True, **kw)
    except OSError:
        return None
