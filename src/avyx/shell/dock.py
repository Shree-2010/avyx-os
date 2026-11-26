"""Floating glass dock with magnification, running indicators, launch bounce and a context menu."""
import math
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gdk, GLib, Gtk, Pango, PangoCairo  # noqa: E402

from .. import apps, config, glass  # noqa: E402
from ..gfx import rrect  # noqa: E402
from .util import BOTTOM, LAYER, Menu, layer_window, set_origin  # noqa: E402

px = config.px

SRC = 128          # source icon size used for scaling


class Item:
    def __init__(self, id, icon, label, app=None):
        self.id, self.icon, self.label, self.app = id, icon, label, app
        self.scale = 1.0
        self.target = 1.0
        self.x = self.w = 0.0
        self.bounce_t0 = None


class Dock:
    def __init__(self, shell):
        self.shell = shell
        self.profile = config.profile()
        self.magnify = config.settings.get("magnify", True) and self.profile != "basic"
        self.B = px(54)
        self.M = 1.62
        self.gap = px(9)
        self.pad = px(12)
        self.sep_w = px(18)
        self.mb = px(10)
        self.items = []
        for i in apps.DOCK_IDS:
            if i == "|":
                it = Item("|", None, "")
            elif i == "launcher":
                it = Item(i, "avyx-launcher", "Launcher")
            elif i == "trash":
                it = Item(i, "trash", "Recycle Bin")
            else:
                a = apps.BY_ID[i]
                it = Item(i, a.icon, a.name, a)
            self.items.append(it)
        n_icons = sum(1 for i in self.items if i.id != "|")
        self.base_w = n_icons * self.B + (len(self.items) - 1) * self.gap + self.sep_w - self.gap + 2 * self.pad
        self.pill_h = self.B + 2 * self.pad
        extra = int(self.B * (self.M - 1) * 3.2) + px(40)
        self.win_w = int(self.base_w + extra)
        self.win_h = int(self.B * self.M + 2 * self.pad + px(46))
        sw, sh = config.Screen.w, config.Screen.h
        self.win = layer_window(shell.app, "avyx-dock", LAYER.TOP, anchors=(BOTTOM,), margins={BOTTOM: self.mb},
                                exclusive=self.pill_h + self.mb)
        set_origin(self.win, (sw - self.win_w) / 2, sh - self.mb - self.win_h)
        self.area = Gtk.DrawingArea()
        self.area.set_content_width(self.win_w)
        self.area.set_content_height(self.win_h)
        self.area.set_draw_func(self._draw)
        self.win.set_child(self.area)

        self.px = None          # pointer x in widget coordinates
        self.hover = None
        mc = Gtk.EventControllerMotion()
        mc.connect("motion", self._motion)
        mc.connect("leave", self._leave)
        self.area.add_controller(mc)
        gc = Gtk.GestureClick()
        gc.set_button(1)
        gc.connect("released", self._click)
        self.area.add_controller(gc)
        rc = Gtk.GestureClick()
        rc.set_button(3)
        rc.connect("pressed", self._context)
        self.area.add_controller(rc)
        self._tick_id = None
        self._layout()
        self.win.connect("realize", self._on_realize)
        self.win.present()
        GLib.timeout_add(700, self._refresh_running)

    # ------------------------------------------------------------------ geometry
    def _on_realize(self, win):
        try:
            import cairo
            surf = win.get_surface()
            y0 = self.win_h - self.pill_h - px(36)
            reg = cairo.Region(cairo.RectangleInt(0, max(0, y0), self.win_w, self.win_h - max(0, y0)))
            surf.set_input_region(reg)
        except Exception as e:  # input region is an optimisation, never fatal
            print("dock: input region unavailable:", e)

    def _layout(self):
        """Compute x/width of every item for the current scales; the pill stays centred in the window."""
        total = 2 * self.pad
        for i, it in enumerate(self.items):
            it.w = self.B * it.scale if it.id != "|" else self.sep_w
            total += it.w + (self.gap if i < len(self.items) - 1 else 0)
        self.pill_w = total
        x = (self.win_w - total) / 2 + self.pad
        for it in self.items:
            it.x = x
            x += it.w + self.gap

    def _targets(self):
        for it in self.items:
            it.target = 1.0
        if self.px is None or not self.magnify:
            return
        # centres of the un-magnified layout
        base_total = self.base_w
        x = (self.win_w - base_total) / 2 + self.pad
        sigma = 1.25 * (self.B + self.gap)
        for it in self.items:
            w = self.B if it.id != "|" else self.sep_w
            cx = x + w / 2
            x += w + self.gap
            if it.id == "|":
                continue
            d = (self.px - cx) / sigma
            it.target = 1.0 + (self.M - 1.0) * math.exp(-d * d)

    # ------------------------------------------------------------------ events
    def _motion(self, ctl, x, y):
        self.px = x
        self._targets()
        self._start_anim()

    def _leave(self, ctl):
        self.px = None
        self.hover = None
        self._targets()
        self._start_anim()

    def test_hover(self, idx):
        """CI hook: pretend the pointer rests on item `idx` (-1 = leave)."""
        if idx < 0:
            self._leave(None)
            return
        it = self.items[idx]
        self.px = it.x + it.w / 2
        self._targets()
        self._start_anim()

    def _start_anim(self):
        if self._tick_id is None:
            self._tick_id = self.area.add_tick_callback(self._tick)

    def _tick(self, widget, clock):
        moving = False
        now = time.monotonic()
        for it in self.items:
            d = it.target - it.scale
            if abs(d) > 0.004:
                it.scale += d * 0.34
                moving = True
            else:
                it.scale = it.target
            if it.bounce_t0 is not None:
                if now - it.bounce_t0 > 1.4:
                    it.bounce_t0 = None
                else:
                    moving = True
        self._layout()
        self.hover = self._hit(self.px) if self.px is not None else None
        self.area.queue_draw()
        if not moving:
            self._tick_id = None
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    def _hit(self, x):
        if x is None:
            return None
        for it in self.items:
            if it.id != "|" and it.x - self.gap / 2 <= x <= it.x + it.w + self.gap / 2:
                return it
        return None

    def _click(self, g, n, x, y):
        it = self._hit(x)
        if not it:
            return
        it.bounce_t0 = time.monotonic()
        self._start_anim()
        if it.id == "launcher":
            self.shell.invoke("launcher")
        elif it.id == "trash":
            self.shell.invoke("path:trash:///")
        else:
            self.shell.launch(it.app)

    def _context(self, g, n, x, y):
        it = self._hit(x)
        if not it:
            return
        items = []
        if it.app is not None:
            items.append(("Open", "open:" + it.id, None))
            if it.app.running():
                items.append(("Quit", "quit:" + it.id, None))
        elif it.id == "trash":
            items.append(("Open Recycle Bin", "path:trash:///", None))
        elif it.id == "launcher":
            items.append(("Open Launcher", "launcher", None))
        if not items:
            return
        m = Menu(self.shell, self.area, items)
        m.pop.set_position(Gtk.PositionType.TOP)
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = int(it.x + it.w / 2), int(self.win_h - self.pad - self.B), 1, 1
        m.pop.set_pointing_to(rect)
        m.popup()

    def _refresh_running(self):
        self.area.queue_draw()
        return True

    # ------------------------------------------------------------------ drawing
    def _draw(self, area, cr, w, h):
        import cairo
        pw, ph = self.pill_w, self.pill_h
        pxl = (w - pw) / 2
        pyl = h - ph
        ox, oy = self.win._origin
        r = ph * 0.34
        bd = glass.get()
        # outer glow
        for i, a in ((6, 0.05), (4, 0.07), (2, 0.10)):
            rrect(cr, pxl - i, pyl - i, pw + 2 * i, ph + 2 * i, r + i)
            cr.set_source_rgba(1.0, 0.54, 0.12, a)
            cr.set_line_width(2)
            cr.stroke()
        # glass body
        rrect(cr, pxl, pyl, pw, ph, r)
        cr.save()
        cr.clip()
        Gdk.cairo_set_source_pixbuf(cr, bd.blurred, -ox, -oy)
        cr.paint()
        cr.set_source_rgba(0.07, 0.055, 0.10, 0.58)
        cr.paint()
        lg = cairo.LinearGradient(0, pyl, 0, pyl + ph)
        lg.add_color_stop_rgba(0, 1, 1, 1, 0.13)
        lg.add_color_stop_rgba(0.5, 1, 1, 1, 0.03)
        lg.add_color_stop_rgba(1, 1, 0.55, 0.15, 0.10)
        cr.set_source(lg)
        cr.paint()
        cr.restore()
        # orange rim
        rrect(cr, pxl + 0.5, pyl + 0.5, pw - 1, ph - 1, r)
        rg = cairo.LinearGradient(0, pyl, 0, pyl + ph)
        rg.add_color_stop_rgba(0, 1.0, 0.62, 0.25, 0.55)
        rg.add_color_stop_rgba(1, 1.0, 0.50, 0.12, 0.95)
        cr.set_source(rg)
        cr.set_line_width(1.6)
        cr.stroke()

        now = time.monotonic()
        base_y = h - self.pad - self.B          # top of an un-magnified icon
        for it in self.items:
            if it.id == "|":
                cr.set_source_rgba(1, 1, 1, 0.22)
                cr.rectangle(it.x + it.w / 2 - 0.5, base_y + self.B * 0.14, 1, self.B * 0.72)
                cr.fill()
                continue
            size = self.B * it.scale
            y = h - self.pad - size
            if it.bounce_t0 is not None:
                t = (now - it.bounce_t0)
                y -= abs(math.sin(t * math.pi * 2.2)) * px(22) * max(0.0, 1.0 - t / 1.4)
            pb = apps.pixbuf(it.icon, SRC)
            if pb:
                cr.save()
                cr.translate(it.x, y)
                k = size / SRC
                cr.scale(k, k)
                Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
                cr.get_source().set_filter(cairo.FILTER_BEST)
                cr.paint()
                cr.restore()
            running = bool(it.app and it.app.running()) or (it.id in self.shell.running_ids())
            if running:
                cr.arc(it.x + it.w / 2, h - px(6), px(2.4), 0, 2 * math.pi)
                cr.set_source_rgba(1, 1, 1, 0.9)
                cr.fill()
        if self.hover is not None:
            self._label(cr, self.hover, h)

    def _label(self, cr, it, h):
        lay = PangoCairo.create_layout(cr)
        fd = Pango.FontDescription()
        fd.set_family("Inter")
        fd.set_weight(Pango.Weight.SEMIBOLD)
        fd.set_absolute_size(px(13) * Pango.SCALE)
        lay.set_font_description(fd)
        lay.set_text(it.label, -1)
        tw, th = lay.get_pixel_size()
        padx, pady = px(12), px(5)
        bw, bh = tw + 2 * padx, th + 2 * pady
        size = self.B * it.scale
        cx = it.x + it.w / 2
        bx = max(px(4), min(self.win_w - bw - px(4), cx - bw / 2))
        by = h - self.pad - size - bh - px(10)
        rrect(cr, bx, by, bw, bh, bh / 2)
        cr.set_source_rgba(0.07, 0.055, 0.10, 0.9)
        cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, 0.14)
        cr.set_line_width(1)
        cr.stroke()
        cr.move_to(bx + padx, by + pady)
        cr.set_source_rgba(1, 1, 1, 0.96)
        PangoCairo.show_layout(cr, lay)
