"""The desktop surface: wallpaper, AVYX wordmark, desktop icons and widgets."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gtk, Pango, PangoCairo  # noqa: E402

from .. import apps, config, glass  # noqa: E402
from .util import BOTTOM, LAYER, LEFT, RIGHT, TOP, layer_window  # noqa: E402
from .widgets import ClockCard, MediaCard, MonitorCard, QuoteCard  # noqa: E402

px = config.px


class Wordmark(Gtk.DrawingArea):
    """'AVYX OS' + slogan, drawn with Pango/cairo (orange gradient on AVYX)."""

    def __init__(self):
        super().__init__()
        self.W, self.H = px(640), px(210)
        self.set_content_width(self.W)
        self.set_content_height(self.H)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        self.set_can_target(False)
        self.set_draw_func(self._draw)

    @staticmethod
    def _layout(cr, text, size, weight, spacing):
        lay = PangoCairo.create_layout(cr)
        fd = Pango.FontDescription()
        fd.set_family("Inter")
        fd.set_weight(weight)
        fd.set_absolute_size(size * Pango.SCALE)
        lay.set_font_description(fd)
        al = Pango.AttrList()
        al.insert(Pango.attr_letter_spacing_new(int(spacing * Pango.SCALE)))
        lay.set_attributes(al)
        lay.set_text(text, -1)
        return lay

    def _draw(self, area, cr, w, h):
        import cairo
        # faint arc halo behind the wordmark
        cr.save()
        cr.set_line_width(1.2)
        for i, (rad, alpha) in enumerate(((h * 1.25, 0.10), (h * 1.05, 0.07))):
            cr.set_source_rgba(1, 1, 1, alpha)
            cr.arc(w * 0.5, h * 1.05, rad, 3.6, 5.8)
            cr.stroke()
        cr.restore()

        size = px(74)
        big = self._layout(cr, "AVYX", size, Pango.Weight.HEAVY, px(5))
        os_ = self._layout(cr, "OS", size, Pango.Weight.LIGHT, px(5))
        bw, bh = big.get_pixel_size()
        ow, oh = os_.get_pixel_size()
        gap = px(22)
        total = bw + gap + ow
        x0 = (w - total) / 2
        y0 = px(14)
        # soft shadow
        for dx, dy, a in ((0, px(3), 0.45), (0, px(7), 0.25)):
            cr.move_to(x0 + dx, y0 + dy)
            cr.set_source_rgba(0, 0, 0, a)
            PangoCairo.show_layout(cr, big)
        lg = cairo.LinearGradient(0, y0, 0, y0 + bh)
        lg.add_color_stop_rgb(0.0, 1.0, 0.80, 0.28)
        lg.add_color_stop_rgb(0.55, 1.0, 0.55, 0.14)
        lg.add_color_stop_rgb(1.0, 1.0, 0.36, 0.10)
        cr.move_to(x0, y0)
        cr.set_source(lg)
        PangoCairo.show_layout(cr, big)
        cr.move_to(x0 + bw + gap + px(1), y0 + px(3) + px(3))
        cr.set_source_rgba(0, 0, 0, 0.4)
        PangoCairo.show_layout(cr, os_)
        cr.move_to(x0 + bw + gap, y0 + px(3))
        cr.set_source_rgba(1, 1, 1, 0.96)
        PangoCairo.show_layout(cr, os_)

        slog = self._layout(cr, "BUILD BEYOND LIMITS", px(15), Pango.Weight.MEDIUM, px(9))
        sw, sh = slog.get_pixel_size()
        sy = y0 + bh + px(18)
        cr.move_to((w - sw) / 2 + px(1), sy + px(1))
        cr.set_source_rgba(0, 0, 0, 0.55)
        PangoCairo.show_layout(cr, slog)
        cr.move_to((w - sw) / 2, sy)
        cr.set_source_rgba(1, 1, 1, 0.88)
        PangoCairo.show_layout(cr, slog)


class Desktop:
    def __init__(self, shell):
        self.shell = shell
        self.win = layer_window(shell.app, "avyx-desktop", LAYER.BACKGROUND, anchors=(TOP, BOTTOM, LEFT, RIGHT), exclusive=-1)
        bd = glass.get()
        ov = Gtk.Overlay()
        pic = Gtk.Picture.new_for_paintable(bd.texture)
        pic.set_content_fit(Gtk.ContentFit.COVER)
        pic.set_can_shrink(True)
        ov.set_child(pic)

        wm = Wordmark()
        wm.set_margin_top(int(config.Screen.h * 0.215))
        wm.set_margin_start(px(40))
        ov.add_overlay(wm)

        # desktop icons
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(12))
        col.set_halign(Gtk.Align.START)
        col.set_valign(Gtk.Align.START)
        col.set_margin_start(px(26))
        col.set_margin_top(px(46))
        for icon, label, cmd in (("this-pc", "This PC", "path:computer:///"), ("folder-home", "Home", "path:~"), ("trash", "Recycle Bin", "path:trash:///")):
            col.append(self._icon(icon, label, cmd))
        ov.add_overlay(col)

        # widgets
        wcol = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(14))
        wcol.set_halign(Gtk.Align.END)
        wcol.set_valign(Gtk.Align.START)
        wcol.set_margin_top(px(46))
        wcol.set_margin_end(px(24))
        self.clock = ClockCard()
        self.media = MediaCard()
        self.monitor = MonitorCard()
        self.quote = QuoteCard()
        wcol.append(self.clock.widget)
        wcol.append(self.media.widget)
        wcol.append(self.monitor.widget)
        wcol.append(self.quote.widget)
        self.wcol = wcol
        wcol.set_visible(bool(config.settings.get("widgets", True)))
        ov.add_overlay(wcol)

        self.win.set_child(ov)
        self.win.present()

    def _icon(self, icon, label, cmd):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(5))
        box.add_css_class("desk-icon")
        box.set_size_request(px(92), -1)
        box.set_margin_top(px(4))
        box.set_margin_bottom(px(4))
        img = apps.icon_widget(icon, px(58))
        box.append(img)
        lab = Gtk.Label(label=label)
        box.append(lab)
        g = Gtk.GestureClick()
        g.connect("pressed", lambda gg, n, x, y, c=cmd: self.shell.invoke(c) if n >= 2 else None)
        box.add_controller(g)
        return box

    def toggle_widgets(self):
        v = not self.wcol.get_visible()
        self.wcol.set_visible(v)
        config.settings.set("widgets", v)
