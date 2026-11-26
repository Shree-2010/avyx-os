"""Desktop widgets: clock/weather, media player, system monitor, quote. All use the shared glass backdrop."""
import math
import os
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import GLib, Gtk  # noqa: E402

from .. import config, glass, sysinfo, weather  # noqa: E402
from ..gfx import Glyph, rrect  # noqa: E402
from ..mpris import Mpris  # noqa: E402

px = config.px


def _vsep():
    s = Gtk.Box()
    s.add_css_class("vsep")
    return s


def _hsep():
    s = Gtk.Box()
    s.add_css_class("hsep")
    return s


def _label(text, css=None, xalign=0.0, wrap=False):
    lab = Gtk.Label(label=text, xalign=xalign)
    if css:
        lab.add_css_class(css)
    if wrap:
        lab.set_wrap(True)
        lab.set_natural_wrap_mode(Gtk.NaturalWrapMode.WORD) if hasattr(Gtk, "NaturalWrapMode") else None
    return lab


class WeatherIcon(Gtk.DrawingArea):
    """Small coloured weather glyph (sun / partly cloudy / cloud / rain)."""

    def __init__(self, size):
        super().__init__()
        self.kind = "cloud-sun"
        self.set_content_width(size)
        self.set_content_height(size)
        self.set_draw_func(self._draw)

    def set_kind(self, k):
        self.kind = k
        self.queue_draw()

    def _draw(self, a, cr, w, h):
        s = min(w, h)
        cr.scale(s, s)
        k = self.kind
        if k in ("sun", "cloud-sun"):
            cx, cy = (0.5, 0.5) if k == "sun" else (0.64, 0.34)
            r = 0.2 if k == "sun" else 0.15
            cr.set_source_rgb(1.0, 0.78, 0.2)
            cr.set_line_width(0.045)
            cr.set_line_cap(1)
            for i in range(8):
                ang = i * math.pi / 4
                cr.move_to(cx + (r + 0.05) * math.cos(ang), cy + (r + 0.05) * math.sin(ang))
                cr.line_to(cx + (r + 0.12) * math.cos(ang), cy + (r + 0.12) * math.sin(ang))
            cr.stroke()
            cr.arc(cx, cy, r, 0, 2 * math.pi)
            cr.set_source_rgb(1.0, 0.82, 0.25)
            cr.fill()
        if k in ("cloud-sun", "cloud", "rain"):
            ox = -0.04 if k == "cloud-sun" else 0.0
            oy = 0.1 if k == "cloud-sun" else 0.0
            cr.new_path()
            cr.arc(0.3 + ox, 0.62 + oy, 0.15, 0, 2 * math.pi)
            cr.arc(0.5 + ox, 0.5 + oy, 0.2, 0, 2 * math.pi)
            cr.arc(0.7 + ox, 0.6 + oy, 0.16, 0, 2 * math.pi)
            cr.rectangle(0.3 + ox, 0.6 + oy, 0.4, 0.17)
            cr.set_source_rgb(0.9, 0.93, 0.98) if k != "rain" else cr.set_source_rgb(0.72, 0.78, 0.88)
            cr.fill()
        if k == "rain":
            cr.set_source_rgb(0.4, 0.7, 1.0)
            cr.set_line_width(0.05)
            cr.set_line_cap(1)
            for x in (0.34, 0.5, 0.66):
                cr.move_to(x, 0.8)
                cr.line_to(x - 0.05, 0.92)
            cr.stroke()


def _tz_city():
    try:
        link = os.path.realpath("/etc/localtime")
        if "zoneinfo/" in link:
            return link.split("zoneinfo/", 1)[1].split("/")[-1].replace("_", " ")
    except OSError:
        pass
    return time.tzname[0]


class ClockCard:
    def __init__(self):
        outer = Gtk.Box(spacing=px(16))
        outer.add_css_class("card")
        for m in ("start", "end", "top", "bottom"):
            getattr(outer, "set_margin_" + m)(px(18))
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(5))
        left.set_size_request(px(214), -1)
        trow = Gtk.Box(valign=Gtk.Align.END)
        self.time = _label("", "time-big")
        self.ampm = _label("", "time-ampm")
        trow.append(self.time)
        trow.append(self.ampm)
        left.append(trow)
        self.date = _label("", "card-date")
        left.append(self.date)
        h1 = _hsep()
        h1.set_margin_top(px(4))
        h1.set_margin_bottom(px(4))
        left.append(h1)
        locrow = Gtk.Box(spacing=px(7))
        pin = Glyph("pin", px(15))
        pin.add_css_class("accent-glyph")
        pin.set_valign(Gtk.Align.CENTER)
        locrow.append(pin)
        self.loc = _label("", "card-loc")
        locrow.append(self.loc)
        left.append(locrow)
        h2 = _hsep()
        h2.set_margin_top(px(4))
        h2.set_margin_bottom(px(2))
        left.append(h2)
        wrow = Gtk.Box(spacing=px(10))
        self.wicon = WeatherIcon(px(44))
        wrow.append(self.wicon)
        wv = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
        self.temp = _label("--°", "temp")
        self.cond = _label("", "cond")
        wv.append(self.temp)
        wv.append(self.cond)
        wrow.append(wv)
        left.append(wrow)
        outer.append(left)
        outer.append(_vsep())
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.START, spacing=px(8))
        right.set_size_request(px(104), -1)
        q = _label("Small steps build limitless futures.", "quote", wrap=True)
        q.set_max_width_chars(11)
        q.set_width_chars(9)
        right.append(q)
        by = _label("—  AVYX OS", "quote-by")
        by.set_margin_top(px(8))
        right.append(by)
        outer.append(right)
        self.widget = glass.glass_box(outer, radius=px(26))
        self.widget.set_size_request(px(360), -1)

        self.loc_info = config.settings.get("location")
        if config.TEST and not self.loc_info:
            self.loc_info = None
            self.loc.set_label("Chennai, IN")
            self.temp.set_label("24°C")
            self.cond.set_label("Partly Cloudy")
            self.wicon.set_kind("cloud-sun")
        elif self.loc_info:
            self.loc.set_label(self.loc_info.get("name", ""))
            self._weather()
            GLib.timeout_add_seconds(1800, self._weather)
        else:
            self.loc.set_label(_tz_city())
            self.cond.set_label("Set location in Settings")
        self.tick()
        GLib.timeout_add(1000, self.tick)

    def _weather(self):
        li = self.loc_info
        if li and "lat" in li and "lon" in li:
            weather.fetch(li["lat"], li["lon"], self._weather_cb)
        return True

    def _weather_cb(self, temp, text, kind):
        self.temp.set_label("%d°C" % round(temp))
        self.cond.set_label(text)
        self.wicon.set_kind(kind)
        return False

    def tick(self):
        now = time.localtime()
        if config.settings.get("clock24"):
            self.time.set_label(time.strftime("%H:%M", now))
            self.ampm.set_label("")
        else:
            self.time.set_label(time.strftime("%-I:%M", now))
            self.ampm.set_label(time.strftime("%p", now))
        self.date.set_label(time.strftime("%A, %B %-d, %Y", now))
        return True


class Wave(Gtk.DrawingArea):
    BARS = (0.35, 0.6, 0.85, 1.0, 0.75, 0.5, 0.3)

    def __init__(self):
        super().__init__()
        self.playing = False
        self.phase = 0.0
        self.set_content_width(px(46))
        self.set_content_height(px(34))
        self.set_draw_func(self._draw)
        self._src = None

    def set_playing(self, p):
        self.playing = p
        if p and not self._src:
            self._src = GLib.timeout_add(110, self._step)
        self.queue_draw()

    def _step(self):
        if not self.playing:
            self._src = None
            return False
        self.phase += 0.55
        self.queue_draw()
        return True

    def _draw(self, a, cr, w, h):
        n = len(self.BARS)
        bw = w / (n * 2 - 1)
        for i, base in enumerate(self.BARS):
            k = base if not self.playing else 0.25 + 0.75 * abs(math.sin(self.phase + i * 0.9)) * base
            bh = max(bw, h * k)
            x = i * bw * 2
            rrect(cr, x, (h - bh) / 2, bw, bh, bw / 2)
            cr.set_source_rgba(1.0, 0.54, 0.12, 0.95 if self.playing else 0.55)
            cr.fill()


class MediaCard:
    def __init__(self):
        self.mp = Mpris(self.refresh)
        outer = Gtk.Box(spacing=px(16))
        outer.add_css_class("card")
        for m in ("start", "end", "top", "bottom"):
            getattr(outer, "set_margin_" + m)(px(16))
        self.art = Gtk.Picture()
        self.art.set_size_request(px(74), px(74))
        self.art.set_can_shrink(False)
        self.art.set_content_fit(Gtk.ContentFit.COVER)
        self.art.add_css_class("art")
        self.art.set_overflow(Gtk.Overflow.HIDDEN)
        from .. import apps
        self.default_art = apps.icon_widget("avyx-mark", px(60))
        self.art_box = Gtk.Overlay()
        self.art_box.set_size_request(px(74), px(74))
        self.art_box.set_valign(Gtk.Align.START)
        self.art_box.set_child(self.art)
        self.art_box.add_overlay(self.default_art)
        outer.append(self.art_box)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, spacing=px(6))
        top = Gtk.Box(spacing=px(10))
        tv = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        self.title = _label("Nothing playing", "track-title")
        self.title.set_ellipsize(3)
        self.title.set_max_width_chars(16)
        self.artist = _label("Open Music to start", "track-artist")
        self.artist.set_ellipsize(3)
        self.artist.set_max_width_chars(18)
        tv.append(self.title)
        tv.append(self.artist)
        top.append(tv)
        self.wave = Wave()
        self.wave.set_valign(Gtk.Align.CENTER)
        top.append(self.wave)
        right.append(top)
        right.append(_hsep())
        ctl = Gtk.Box(spacing=px(6), halign=Gtk.Align.FILL)
        ctl.set_homogeneous(False)
        spacer1 = Gtk.Box(hexpand=True)
        spacer2 = Gtk.Box(hexpand=True)
        ctl.append(self._ctl("shuffle", None))
        ctl.append(spacer1)
        ctl.append(self._ctl("prev", self.mp.previous))
        self.play_btn = Gtk.Button()
        self.play_btn.add_css_class("playbtn")
        self.play_glyph = Glyph("play", px(18))
        self.play_btn.set_child(self.play_glyph)
        self.play_btn.connect("clicked", lambda *_: self.mp.play_pause())
        ctl.append(self.play_btn)
        ctl.append(self._ctl("next", self.mp.next))
        ctl.append(spacer2)
        ctl.append(self._ctl("repeat", None))
        right.append(ctl)
        outer.append(right)
        self.widget = glass.glass_box(outer, radius=px(26))
        self.widget.set_size_request(px(360), -1)
        if config.TEST:
            self.title.set_label("Good Things")
            self.artist.set_label("AVYX")
            self.play_glyph.set_glyph("pause")
            self.wave.set_playing(False)
            self.wave.phase = 0.6
        self.refresh()

    def _ctl(self, name, cb):
        b = Gtk.Button()
        b.add_css_class("ctl")
        b.set_child(Glyph(name, px(17)))
        if cb:
            b.connect("clicked", lambda *_: cb())
        else:
            b.set_sensitive(False)
            b.set_opacity(0.7)
        return b

    def refresh(self):
        mp = self.mp
        if mp.proxy:
            self.title.set_label(mp.title or "Unknown track")
            self.artist.set_label(mp.artist or "")
            playing = mp.status == "Playing"
            self.play_glyph.set_glyph("pause" if playing else "play")
            self.wave.set_playing(playing)
            if mp.art and os.path.exists(mp.art):
                self.art.set_filename(mp.art)
                self.default_art.set_visible(False)
            else:
                self.art.set_paintable(None)
                self.default_art.set_visible(True)
        elif not config.TEST:
            self.title.set_label("Nothing playing")
            self.artist.set_label("Open Music to start")
            self.play_glyph.set_glyph("play")
            self.wave.set_playing(False)
            self.default_art.set_visible(True)


class MonitorCard:
    def __init__(self):
        self.cpu = sysinfo.CpuSampler()
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(8))
        outer.add_css_class("card")
        for m in ("start", "end"):
            getattr(outer, "set_margin_" + m)(px(20))
        outer.set_margin_top(px(16))
        outer.set_margin_bottom(px(18))
        head = Gtk.Box(spacing=px(9))
        g = Glyph("activity", px(19))
        g.add_css_class("accent-glyph")
        head.append(g)
        head.append(_label("System Monitor", "mon-title"))
        outer.append(head)
        self.rows = {}
        for key, name, css in (("cpu", "CPU", "cpu"), ("ram", "RAM", "ram"), ("sto", "Storage", "sto")):
            row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(4))
            top = Gtk.Box()
            nm = _label(name, "mon-name")
            nm.set_hexpand(True)
            val = _label("0%", "mon-val", xalign=1.0)
            top.append(nm)
            top.append(val)
            bar = Gtk.ProgressBar()
            bar.add_css_class("mon")
            bar.add_css_class(css)
            row.append(top)
            row.append(bar)
            outer.append(row)
            self.rows[key] = (val, bar)
        self.widget = glass.glass_box(outer, radius=px(24))
        self.widget.set_size_request(px(360), -1)
        self.update()
        GLib.timeout_add_seconds(2, self.update)

    def update(self):
        vals = {"cpu": self.cpu.percent(), "ram": sysinfo.mem_percent()[0], "sto": sysinfo.disk_percent("/")[0]}
        if config.TEST:
            vals = {"cpu": 12.0, "ram": 46.0, "sto": 74.0}
        for k, v in vals.items():
            lab, bar = self.rows[k]
            lab.set_label("%d%%" % round(v))
            bar.set_fraction(max(0.0, min(1.0, v / 100.0)))
        return True


class QuoteCard:
    def __init__(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(4), valign=Gtk.Align.CENTER)
        outer.add_css_class("card")
        for m in ("start", "end"):
            getattr(outer, "set_margin_" + m)(px(20))
        outer.set_margin_top(px(16))
        outer.set_margin_bottom(px(16))
        q = _label("Dream Bigger,\nBuild Better.", "big-quote")
        outer.append(q)
        line = Gtk.Box()
        line.add_css_class("accent-line")
        line.set_size_request(px(44), px(3))
        line.set_halign(Gtk.Align.START)
        line.set_margin_top(px(6))
        outer.append(line)
        self.widget = glass.glass_box(outer, radius=px(24))
        self.widget.set_size_request(px(360), -1)
