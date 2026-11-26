"""Vector glyphs drawn with cairo (follow the widget's CSS colour) and small drawing helpers."""
import math

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402


def rrect(cr, x, y, w, h, r):
    r = max(0.0, min(r, w / 2, h / 2))
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def _pen(cr, w=0.09):
    cr.set_line_width(w)
    cr.set_line_cap(1)   # round
    cr.set_line_join(1)  # round


# ---------------------------------------------------------------- glyphs (unit square, caller sets colour)
def g_wifi(cr, v=None):
    _pen(cr, 0.11)
    for r in (0.62, 0.40, 0.19):
        cr.new_path()
        cr.arc(0.5, 0.86, r, math.radians(228), math.radians(312))
        cr.stroke()
    cr.new_path()
    cr.arc(0.5, 0.86, 0.065, 0, 2 * math.pi)
    cr.fill()


def g_wifi_off(cr, v=None):
    g_wifi(cr)
    _pen(cr, 0.1)
    cr.move_to(0.12, 0.1)
    cr.line_to(0.9, 0.92)
    cr.stroke()


def g_ethernet(cr, v=None):
    _pen(cr, 0.09)
    rrect(cr, 0.18, 0.14, 0.64, 0.42, 0.06)
    cr.stroke()
    cr.move_to(0.5, 0.56)
    cr.line_to(0.5, 0.78)
    cr.move_to(0.22, 0.78)
    cr.line_to(0.78, 0.78)
    cr.move_to(0.22, 0.78)
    cr.line_to(0.22, 0.9)
    cr.move_to(0.78, 0.78)
    cr.line_to(0.78, 0.9)
    cr.stroke()


def g_bluetooth(cr, v=None):
    _pen(cr, 0.09)
    cr.move_to(0.26, 0.3)
    cr.line_to(0.74, 0.7)
    cr.line_to(0.5, 0.92)
    cr.line_to(0.5, 0.08)
    cr.line_to(0.74, 0.3)
    cr.line_to(0.26, 0.7)
    cr.stroke()


def g_volume(cr, v=None):
    cr.move_to(0.1, 0.38)
    cr.line_to(0.3, 0.38)
    cr.line_to(0.5, 0.2)
    cr.line_to(0.5, 0.8)
    cr.line_to(0.3, 0.62)
    cr.line_to(0.1, 0.62)
    cr.close_path()
    cr.fill()
    _pen(cr, 0.085)
    for r, a in ((0.2, 44), (0.37, 48)):
        cr.new_path()
        cr.arc(0.5, 0.5, r, math.radians(-a), math.radians(a))
        cr.stroke()


def g_volume_mute(cr, v=None):
    cr.move_to(0.1, 0.38)
    cr.line_to(0.3, 0.38)
    cr.line_to(0.5, 0.2)
    cr.line_to(0.5, 0.8)
    cr.line_to(0.3, 0.62)
    cr.line_to(0.1, 0.62)
    cr.close_path()
    cr.fill()
    _pen(cr, 0.085)
    cr.move_to(0.66, 0.36)
    cr.line_to(0.9, 0.64)
    cr.move_to(0.9, 0.36)
    cr.line_to(0.66, 0.64)
    cr.stroke()


def g_battery(cr, v=None):
    level = 0.8 if v is None else max(0.0, min(1.0, v))
    _pen(cr, 0.07)
    rrect(cr, 0.04, 0.27, 0.8, 0.46, 0.1)
    cr.stroke()
    rrect(cr, 0.88, 0.41, 0.08, 0.18, 0.03)
    cr.fill()
    if level > 0:
        rrect(cr, 0.1, 0.33, 0.68 * level, 0.34, 0.05)
        cr.fill()


def g_search(cr, v=None):
    _pen(cr, 0.1)
    cr.new_path()
    cr.arc(0.43, 0.43, 0.28, 0, 2 * math.pi)
    cr.stroke()
    cr.move_to(0.64, 0.64)
    cr.line_to(0.9, 0.9)
    cr.stroke()


def g_chev_r(cr, v=None):
    _pen(cr, 0.11)
    cr.move_to(0.36, 0.2)
    cr.line_to(0.66, 0.5)
    cr.line_to(0.36, 0.8)
    cr.stroke()


def g_chev_l(cr, v=None):
    _pen(cr, 0.11)
    cr.move_to(0.64, 0.2)
    cr.line_to(0.34, 0.5)
    cr.line_to(0.64, 0.8)
    cr.stroke()


def g_home(cr, v=None):
    _pen(cr, 0.09)
    cr.move_to(0.1, 0.5)
    cr.line_to(0.5, 0.14)
    cr.line_to(0.9, 0.5)
    cr.move_to(0.2, 0.44)
    cr.line_to(0.2, 0.86)
    cr.line_to(0.8, 0.86)
    cr.line_to(0.8, 0.44)
    cr.stroke()


def g_home_fill(cr, v=None):
    cr.move_to(0.08, 0.52)
    cr.line_to(0.5, 0.12)
    cr.line_to(0.92, 0.52)
    cr.line_to(0.8, 0.52)
    cr.line_to(0.8, 0.88)
    cr.line_to(0.6, 0.88)
    cr.line_to(0.6, 0.62)
    cr.line_to(0.4, 0.62)
    cr.line_to(0.4, 0.88)
    cr.line_to(0.2, 0.88)
    cr.line_to(0.2, 0.52)
    cr.close_path()
    cr.fill()


def g_folder(cr, v=None):
    _pen(cr, 0.08)
    cr.move_to(0.1, 0.24)
    cr.line_to(0.4, 0.24)
    cr.line_to(0.5, 0.36)
    cr.line_to(0.9, 0.36)
    cr.line_to(0.9, 0.8)
    cr.line_to(0.1, 0.8)
    cr.close_path()
    cr.stroke()


def g_window(cr, v=None):
    _pen(cr, 0.08)
    rrect(cr, 0.1, 0.18, 0.8, 0.64, 0.08)
    cr.stroke()
    cr.move_to(0.1, 0.38)
    cr.line_to(0.9, 0.38)
    cr.stroke()


def g_doc(cr, v=None):
    _pen(cr, 0.08)
    rrect(cr, 0.2, 0.1, 0.6, 0.8, 0.08)
    cr.stroke()
    for y in (0.36, 0.52, 0.68):
        cr.move_to(0.34, y)
        cr.line_to(0.66, y)
    cr.stroke()


def g_download(cr, v=None):
    _pen(cr, 0.09)
    rrect(cr, 0.1, 0.1, 0.8, 0.8, 0.14)
    cr.stroke()
    cr.move_to(0.5, 0.28)
    cr.line_to(0.5, 0.66)
    cr.move_to(0.34, 0.52)
    cr.line_to(0.5, 0.68)
    cr.line_to(0.66, 0.52)
    cr.stroke()


def g_music(cr, v=None):
    cr.new_path()
    cr.arc(0.3, 0.76, 0.14, 0, 2 * math.pi)
    cr.fill()
    cr.new_path()
    cr.arc(0.72, 0.68, 0.14, 0, 2 * math.pi)
    cr.fill()
    cr.rectangle(0.38, 0.2, 0.07, 0.56)
    cr.fill()
    cr.rectangle(0.8, 0.12, 0.07, 0.56)
    cr.fill()
    cr.move_to(0.38, 0.2)
    cr.line_to(0.87, 0.12)
    cr.line_to(0.87, 0.26)
    cr.line_to(0.38, 0.34)
    cr.close_path()
    cr.fill()


def g_picture(cr, v=None):
    _pen(cr, 0.08)
    rrect(cr, 0.1, 0.18, 0.8, 0.64, 0.08)
    cr.stroke()
    cr.move_to(0.14, 0.74)
    cr.line_to(0.38, 0.46)
    cr.line_to(0.54, 0.64)
    cr.line_to(0.66, 0.52)
    cr.line_to(0.86, 0.74)
    cr.stroke()


def g_video(cr, v=None):
    rrect(cr, 0.1, 0.2, 0.8, 0.6, 0.1)
    cr.fill()


def g_trash(cr, v=None):
    _pen(cr, 0.08)
    cr.move_to(0.18, 0.26)
    cr.line_to(0.82, 0.26)
    cr.move_to(0.4, 0.26)
    cr.line_to(0.4, 0.16)
    cr.line_to(0.6, 0.16)
    cr.line_to(0.6, 0.26)
    cr.stroke()
    cr.move_to(0.26, 0.26)
    cr.line_to(0.3, 0.86)
    cr.line_to(0.7, 0.86)
    cr.line_to(0.74, 0.26)
    cr.stroke()


def g_gear(cr, v=None):
    cx = cy = 0.5
    teeth = 8
    pts = []
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        w = math.pi / teeth
        for da, r in ((-0.62 * w, 0.31), (-0.36 * w, 0.43), (0.36 * w, 0.43), (0.62 * w, 0.31)):
            pts.append((cx + r * math.cos(a + da), cy + r * math.sin(a + da)))
    cr.new_path()
    cr.move_to(*pts[0])
    for p in pts[1:]:
        cr.line_to(*p)
    cr.close_path()
    cr.new_sub_path()
    cr.arc(cx, cy, 0.14, 0, 2 * math.pi)
    cr.set_fill_rule(1)  # even-odd
    cr.fill()
    cr.set_fill_rule(0)


def g_info(cr, v=None):
    _pen(cr, 0.08)
    cr.new_path()
    cr.arc(0.5, 0.5, 0.38, 0, 2 * math.pi)
    cr.stroke()
    cr.move_to(0.5, 0.46)
    cr.line_to(0.5, 0.7)
    cr.stroke()
    cr.new_path()
    cr.arc(0.5, 0.31, 0.05, 0, 2 * math.pi)
    cr.fill()


def g_lock(cr, v=None):
    _pen(cr, 0.08)
    rrect(cr, 0.2, 0.44, 0.6, 0.44, 0.08)
    cr.stroke()
    cr.new_path()
    cr.arc(0.5, 0.42, 0.18, math.pi, 2 * math.pi)
    cr.stroke()


def g_logout(cr, v=None):
    _pen(cr, 0.085)
    cr.move_to(0.46, 0.16)
    cr.line_to(0.2, 0.16)
    cr.line_to(0.2, 0.84)
    cr.line_to(0.46, 0.84)
    cr.move_to(0.4, 0.5)
    cr.line_to(0.88, 0.5)
    cr.move_to(0.72, 0.32)
    cr.line_to(0.9, 0.5)
    cr.line_to(0.72, 0.68)
    cr.stroke()


def g_power(cr, v=None):
    _pen(cr, 0.1)
    cr.new_path()
    cr.arc(0.5, 0.54, 0.32, math.radians(-60), math.radians(240))
    cr.stroke()
    cr.move_to(0.5, 0.1)
    cr.line_to(0.5, 0.5)
    cr.stroke()


def g_grid(cr, v=None):
    for x in (0.16, 0.55):
        for y in (0.16, 0.55):
            rrect(cr, x, y, 0.29, 0.29, 0.07)
            cr.fill()


def g_list(cr, v=None):
    _pen(cr, 0.09)
    for y in (0.24, 0.5, 0.76):
        cr.move_to(0.34, y)
        cr.line_to(0.88, y)
        cr.stroke()
        cr.new_path()
        cr.arc(0.15, y, 0.045, 0, 2 * math.pi)
        cr.fill()


def g_prev(cr, v=None):
    cr.rectangle(0.18, 0.22, 0.09, 0.56)
    cr.fill()
    cr.move_to(0.8, 0.22)
    cr.line_to(0.34, 0.5)
    cr.line_to(0.8, 0.78)
    cr.close_path()
    cr.fill()


def g_next(cr, v=None):
    cr.rectangle(0.73, 0.22, 0.09, 0.56)
    cr.fill()
    cr.move_to(0.2, 0.22)
    cr.line_to(0.66, 0.5)
    cr.line_to(0.2, 0.78)
    cr.close_path()
    cr.fill()


def g_play(cr, v=None):
    cr.move_to(0.28, 0.16)
    cr.line_to(0.84, 0.5)
    cr.line_to(0.28, 0.84)
    cr.close_path()
    cr.fill()


def g_pause(cr, v=None):
    rrect(cr, 0.24, 0.16, 0.18, 0.68, 0.05)
    cr.fill()
    rrect(cr, 0.58, 0.16, 0.18, 0.68, 0.05)
    cr.fill()


def g_shuffle(cr, v=None):
    _pen(cr, 0.085)
    cr.move_to(0.1, 0.3)
    cr.curve_to(0.4, 0.3, 0.5, 0.7, 0.8, 0.7)
    cr.move_to(0.1, 0.7)
    cr.curve_to(0.4, 0.7, 0.5, 0.3, 0.8, 0.3)
    cr.stroke()
    for y in (0.3, 0.7):
        cr.move_to(0.68, y - 0.12)
        cr.line_to(0.86, y)
        cr.line_to(0.68, y + 0.12)
        cr.stroke()


def g_repeat(cr, v=None):
    _pen(cr, 0.085)
    rrect(cr, 0.12, 0.28, 0.76, 0.44, 0.18)
    cr.stroke()
    cr.move_to(0.6, 0.14)
    cr.line_to(0.76, 0.28)
    cr.line_to(0.6, 0.42)
    cr.stroke()


def g_pin(cr, v=None):
    cr.move_to(0.5, 0.94)
    cr.curve_to(0.2, 0.62, 0.18, 0.5, 0.18, 0.4)
    cr.curve_to(0.18, 0.2, 0.34, 0.06, 0.5, 0.06)
    cr.curve_to(0.66, 0.06, 0.82, 0.2, 0.82, 0.4)
    cr.curve_to(0.82, 0.5, 0.8, 0.62, 0.5, 0.94)
    cr.close_path()
    cr.new_sub_path()
    cr.arc(0.5, 0.4, 0.13, 0, 2 * math.pi)
    cr.set_fill_rule(1)
    cr.fill()
    cr.set_fill_rule(0)


def g_activity(cr, v=None):
    _pen(cr, 0.09)
    cr.move_to(0.04, 0.54)
    cr.line_to(0.26, 0.54)
    cr.line_to(0.38, 0.2)
    cr.line_to(0.56, 0.82)
    cr.line_to(0.68, 0.4)
    cr.line_to(0.76, 0.54)
    cr.line_to(0.96, 0.54)
    cr.stroke()


def g_sun(cr, v=None):
    _pen(cr, 0.08)
    cr.new_path()
    cr.arc(0.5, 0.5, 0.2, 0, 2 * math.pi)
    cr.stroke()
    for i in range(8):
        a = i * math.pi / 4
        cr.move_to(0.5 + 0.3 * math.cos(a), 0.5 + 0.3 * math.sin(a))
        cr.line_to(0.5 + 0.42 * math.cos(a), 0.5 + 0.42 * math.sin(a))
    cr.stroke()


def g_moon(cr, v=None):
    cr.new_path()
    cr.arc(0.5, 0.5, 0.38, math.radians(70), math.radians(330))
    cr.arc_negative(0.62, 0.4, 0.3, math.radians(330 - 40), math.radians(70 + 8))
    cr.close_path()
    cr.fill()


def g_plus(cr, v=None):
    _pen(cr, 0.1)
    cr.move_to(0.5, 0.2)
    cr.line_to(0.5, 0.8)
    cr.move_to(0.2, 0.5)
    cr.line_to(0.8, 0.5)
    cr.stroke()


def g_cross(cr, v=None):
    _pen(cr, 0.1)
    cr.move_to(0.24, 0.24)
    cr.line_to(0.76, 0.76)
    cr.move_to(0.76, 0.24)
    cr.line_to(0.24, 0.76)
    cr.stroke()


def g_check(cr, v=None):
    _pen(cr, 0.11)
    cr.move_to(0.2, 0.54)
    cr.line_to(0.42, 0.74)
    cr.line_to(0.82, 0.28)
    cr.stroke()


def g_bell(cr, v=None):
    _pen(cr, 0.08)
    cr.move_to(0.22, 0.72)
    cr.curve_to(0.3, 0.64, 0.3, 0.52, 0.3, 0.42)
    cr.curve_to(0.3, 0.26, 0.4, 0.18, 0.5, 0.18)
    cr.curve_to(0.6, 0.18, 0.7, 0.26, 0.7, 0.42)
    cr.curve_to(0.7, 0.52, 0.7, 0.64, 0.78, 0.72)
    cr.close_path()
    cr.stroke()
    cr.new_path()
    cr.arc(0.5, 0.82, 0.07, 0, math.pi)
    cr.fill()


def g_cloud(cr, v=None):
    cr.new_path()
    cr.arc(0.32, 0.6, 0.16, 0, 2 * math.pi)
    cr.arc(0.5, 0.46, 0.2, 0, 2 * math.pi)
    cr.arc(0.7, 0.58, 0.17, 0, 2 * math.pi)
    cr.rectangle(0.32, 0.6, 0.38, 0.17)
    cr.fill()


def g_dots(cr, v=None):
    for x in (0.2, 0.5, 0.8):
        cr.new_path()
        cr.arc(x, 0.5, 0.075, 0, 2 * math.pi)
        cr.fill()


GLYPHS = {
    "wifi": g_wifi, "wifi-off": g_wifi_off, "ethernet": g_ethernet, "bluetooth": g_bluetooth,
    "volume": g_volume, "volume-mute": g_volume_mute, "battery": g_battery, "search": g_search,
    "chev-r": g_chev_r, "chev-l": g_chev_l, "home": g_home, "home-fill": g_home_fill, "folder": g_folder,
    "window": g_window, "doc": g_doc, "download": g_download, "music": g_music, "picture": g_picture,
    "video": g_video, "trash": g_trash, "gear": g_gear, "info": g_info, "lock": g_lock, "logout": g_logout,
    "power": g_power, "grid": g_grid, "list": g_list, "prev": g_prev, "next": g_next, "play": g_play,
    "pause": g_pause, "shuffle": g_shuffle, "repeat": g_repeat, "pin": g_pin, "activity": g_activity,
    "sun": g_sun, "moon": g_moon, "plus": g_plus, "cross": g_cross, "check": g_check, "bell": g_bell,
    "cloud": g_cloud, "dots": g_dots,
}


class Glyph(Gtk.DrawingArea):
    """A square vector icon that takes its colour from the CSS `color` of the widget."""

    def __init__(self, name, size=16, value=None, css=None):
        super().__init__()
        self.name = name
        self.value = value
        self.set_content_width(int(size))
        self.set_content_height(int(size))
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        if css:
            self.add_css_class(css)
        self.set_draw_func(self._draw)

    def set_glyph(self, name, value=None):
        self.name = name
        self.value = value
        self.queue_draw()

    def set_value(self, value):
        self.value = value
        self.queue_draw()

    def _draw(self, area, cr, w, h):
        c = self.get_color()
        cr.set_source_rgba(c.red, c.green, c.blue, c.alpha)
        s = min(w, h)
        cr.translate((w - s) / 2, (h - s) / 2)
        cr.scale(s, s)
        fn = GLYPHS.get(self.name)
        if fn:
            fn(cr, self.value)
