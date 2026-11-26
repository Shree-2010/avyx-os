"""Pre-blurred wallpaper backdrop and a drawing widget that paints 'glass' panels from it.

The compositor does not blur what is behind our surfaces, so every shell panel paints the matching crop of a
blurred copy of the wallpaper (we know exactly where the panel sits on the screen)."""
import math

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, Gtk  # noqa: E402

from . import config  # noqa: E402
from .gfx import rrect  # noqa: E402

_backdrop = None


class Backdrop:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        path = config.wallpaper_path()
        self.path = path
        if path:
            wp = GdkPixbuf.Pixbuf.new_from_file(path)
        else:
            wp = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 64, 64)
            wp.fill(0x1a1428ff)
        k = max(sw / wp.get_width(), sh / wp.get_height())
        w2, h2 = int(math.ceil(wp.get_width() * k)), int(math.ceil(wp.get_height() * k))
        big = wp.scale_simple(w2, h2, GdkPixbuf.InterpType.BILINEAR)
        x0, y0 = (w2 - sw) // 2, (h2 - sh) // 2
        self.sharp = big.new_subpixbuf(x0, y0, sw, sh).copy()
        small = self.sharp.scale_simple(max(8, sw // 18), max(8, sh // 18), GdkPixbuf.InterpType.BILINEAR)
        mid = small.scale_simple(max(16, sw // 6), max(16, sh // 6), GdkPixbuf.InterpType.BILINEAR)
        self.blurred = mid.scale_simple(sw, sh, GdkPixbuf.InterpType.BILINEAR)
        self.texture = Gdk.Texture.new_for_pixbuf(self.sharp)


def get():
    global _backdrop
    if _backdrop is None:
        _backdrop = Backdrop(config.Screen.w, config.Screen.h)
    return _backdrop


def origin_of(widget):
    """Screen position of a widget's top-left corner (windows record their own origin in `_origin`)."""
    root = widget.get_root()
    ox, oy = getattr(root, "_origin", (0, 0))
    if root is None:
        return ox, oy
    r = widget.translate_coordinates(root, 0, 0)
    if r is None:
        return ox, oy
    return ox + r[0], oy + r[1]


class GlassArea(Gtk.DrawingArea):
    """Rounded translucent panel. Draw it as the bottom child of a Gtk.Overlay."""

    def __init__(self, radius=24, tint=(0.075, 0.06, 0.11, 0.56), rim=0.16, glow=None, sheen=0.10):
        super().__init__()
        self.radius = radius
        self.tint = tint
        self.rim = rim
        self.glow = glow         # (r,g,b,a) outer ring colour, e.g. the orange dock rim
        self.sheen = sheen
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_draw_func(self._draw)

    def _draw(self, area, cr, w, h):
        r = self.radius
        ox, oy = origin_of(self)
        bd = get()
        rrect(cr, 0.5, 0.5, w - 1, h - 1, r)
        cr.save()
        cr.clip_preserve()
        Gdk.cairo_set_source_pixbuf(cr, bd.blurred, -ox, -oy)
        cr.paint()
        cr.restore()
        cr.save()
        rrect(cr, 0.5, 0.5, w - 1, h - 1, r)
        cr.clip()
        cr.set_source_rgba(*self.tint)
        cr.paint()
        if self.sheen:
            import cairo
            lg = cairo.LinearGradient(0, 0, 0, h)
            lg.add_color_stop_rgba(0, 1, 1, 1, self.sheen)
            lg.add_color_stop_rgba(0.35, 1, 1, 1, self.sheen * 0.25)
            lg.add_color_stop_rgba(1, 1, 1, 1, 0)
            cr.set_source(lg)
            cr.paint()
        cr.restore()
        # rim
        rrect(cr, 0.5, 0.5, w - 1, h - 1, r)
        if self.glow:
            cr.set_source_rgba(*self.glow)
            cr.set_line_width(1.6)
        else:
            cr.set_source_rgba(1, 1, 1, self.rim)
            cr.set_line_width(1.0)
        cr.stroke()


def glass_box(child, **kw):
    """Wrap a widget in a Gtk.Overlay with a glass panel behind it."""
    ov = Gtk.Overlay()
    ov.set_child(GlassArea(**kw))
    ov.add_overlay(child)
    ov.set_measure_overlay(child, True)
    return ov
