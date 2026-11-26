"""CSS for the AVYX shell and apps (dark glass, orange accent, Inter)."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from .config import px  # noqa: E402

TEXT = "#f6f1ff"
DIM = "rgba(246,241,255,0.62)"
ACC = "#ff8a1f"


def build_css():
    return f"""
* {{ font-family: Inter, "Noto Sans", "DejaVu Sans", sans-serif; }}
window.avyx-layer, window.avyx-layer > * {{ background: transparent; color: {TEXT}; }}
window.avyx-layer label {{ color: inherit; }}

button.avx {{ all: unset; color: {TEXT}; }}
button.avx:focus-visible {{ outline: 2px solid rgba(255,138,31,0.7); outline-offset: -2px; }}

/* ---------------------------------------------------------------- top bar */
.topbar {{ background: rgba(14,11,24,0.66); border-bottom: 1px solid rgba(255,255,255,0.07); }}
.topbar label {{ font-size: {px(13)}px; font-weight: 600; }}
.brand-text {{ font-size: {px(13)}px; font-weight: 700; letter-spacing: {px(4)}px; }}
.brand-sep {{ background: rgba(255,255,255,0.16); min-width: 1px; margin: {px(7)}px {px(12)}px; }}
button.menu {{ padding: 0 {px(11)}px; border-radius: {px(7)}px; min-height: {px(22)}px; }}
button.menu label {{ font-size: {px(13)}px; font-weight: 500; }}
button.menu.app label {{ font-weight: 700; }}
button.menu:hover, button.menu.open {{ background: rgba(255,255,255,0.12); }}
button.status {{ padding: 0 {px(7)}px; border-radius: {px(7)}px; min-height: {px(22)}px; }}
button.status:hover {{ background: rgba(255,255,255,0.12); }}
.dot-accent {{ background: {ACC}; border-radius: 99px; min-width: {px(9)}px; min-height: {px(9)}px; box-shadow: 0 0 {px(8)}px rgba(255,138,31,0.8); }}
.pill {{ background: rgba(0,0,0,0.55); border: 1px solid rgba(255,255,255,0.10); border-radius: 99px; padding: 0 {px(14)}px; min-height: {px(20)}px; }}
.pill label {{ font-size: {px(12)}px; font-weight: 600; }}

/* ---------------------------------------------------------------- popovers & menus */
popover > contents {{ background: rgba(26,20,40,0.94); color: {TEXT}; border: 1px solid rgba(255,255,255,0.12);
    border-radius: {px(12)}px; padding: {px(6)}px; box-shadow: 0 {px(14)}px {px(40)}px rgba(0,0,0,0.55); }}
popover arrow {{ background: transparent; }}
button.mi {{ all: unset; padding: {px(7)}px {px(12)}px; border-radius: {px(7)}px; min-width: {px(170)}px; color: {TEXT}; }}
button.mi:hover {{ background: rgba(255,138,31,0.85); color: #1b1020; }}
button.mi label {{ font-size: {px(13)}px; font-weight: 500; }}
button.mi .key {{ opacity: 0.55; font-size: {px(12)}px; }}
separator.mi {{ background: rgba(255,255,255,0.12); min-height: 1px; margin: {px(4)}px {px(6)}px; }}

/* ---------------------------------------------------------------- desktop */
.desk-icon label {{ font-size: {px(13)}px; font-weight: 500; color: #fff; text-shadow: 0 1px {px(4)}px rgba(0,0,0,0.9), 0 0 {px(2)}px rgba(0,0,0,0.9); }}
.desk-icon:hover {{ background: rgba(255,255,255,0.10); border-radius: {px(10)}px; }}

.card label {{ color: {TEXT}; }}
.time-big {{ font-size: {px(46)}px; font-weight: 500; }}
.time-ampm {{ font-size: {px(19)}px; font-weight: 500; margin-bottom: {px(7)}px; margin-left: {px(4)}px; }}
.card-date {{ font-size: {px(14)}px; color: rgba(246,241,255,0.85); }}
.card-loc {{ font-size: {px(13)}px; color: rgba(246,241,255,0.82); }}
.temp {{ font-size: {px(21)}px; font-weight: 600; }}
.cond {{ font-size: {px(13)}px; color: {DIM}; }}
.quote {{ font-size: {px(18)}px; font-weight: 500; line-height: 1.25; }}
.quote-by {{ font-size: {px(12)}px; color: {DIM}; letter-spacing: {px(1)}px; }}
.vsep {{ background: rgba(255,255,255,0.14); min-width: 1px; }}
.hsep {{ background: rgba(255,255,255,0.12); min-height: 1px; }}
.track-title {{ font-size: {px(15)}px; font-weight: 500; }}
.track-artist {{ font-size: {px(13)}px; color: {DIM}; }}
button.ctl {{ all: unset; color: rgba(246,241,255,0.9); padding: {px(6)}px; border-radius: 99px; }}
button.ctl:hover {{ background: rgba(255,255,255,0.12); }}
button.playbtn {{ all: unset; background: linear-gradient(#ffa23a, #ff6a10); border-radius: 99px; min-width: {px(40)}px; min-height: {px(40)}px;
    box-shadow: 0 0 {px(14)}px rgba(255,120,20,0.75); color: #fff; }}
.mon-title {{ font-size: {px(14)}px; font-weight: 500; }}
.mon-name, .mon-val {{ font-size: {px(13)}px; font-weight: 500; }}
progressbar.mon trough {{ background: rgba(255,255,255,0.12); border-radius: 99px; min-height: {px(8)}px; border: none; }}
progressbar.mon progress {{ border-radius: 99px; min-height: {px(8)}px; border: none; }}
progressbar.cpu progress {{ background: linear-gradient(90deg, #ff9a2e, #ff7a1a); }}
progressbar.ram progress {{ background: linear-gradient(90deg, #1aa0ff, #0a84ff); }}
progressbar.sto progress {{ background: linear-gradient(90deg, #b56cff, #8e4ff0); }}
.big-quote {{ font-size: {px(21)}px; font-weight: 600; }}

.accent-glyph {{ color: {ACC}; }}
.accent-line {{ background: linear-gradient(90deg, #ff9a2e, #ff6a10); border-radius: 99px; }}
picture.art {{ border-radius: {px(14)}px; }}

/* ---------------------------------------------------------------- launcher */
.search-field {{ background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 99px; padding: 0 {px(14)}px; min-height: {px(38)}px; }}
.search-field entry, .search-field entry:focus {{ all: unset; color: {TEXT}; font-size: {px(15)}px; }}
.search-field entry placeholder {{ color: {DIM}; }}
.kbd {{ background: rgba(255,255,255,0.12); border-radius: {px(9)}px; padding: {px(3)}px {px(9)}px; font-size: {px(12)}px; color: {DIM}; }}
button.cat {{ all: unset; padding: {px(8)}px {px(12)}px; border-radius: {px(11)}px; color: {TEXT}; border: 1px solid transparent; }}
button.cat label {{ font-size: {px(15)}px; font-weight: 500; }}
button.cat:hover {{ background: rgba(255,255,255,0.08); }}
button.cat.sel {{ background: linear-gradient(rgba(255,150,40,0.55), rgba(255,110,20,0.38)); border: 1px solid rgba(255,170,80,0.85);
    box-shadow: 0 0 {px(14)}px rgba(255,120,20,0.45), inset 0 1px 0 rgba(255,255,255,0.25); }}
button.cat.danger label {{ color: #ff6258; }}
button.cat.danger .glyph {{ color: #ff6258; }}
button.row {{ all: unset; padding: {px(7)}px {px(10)}px; border-radius: {px(10)}px; color: {TEXT}; }}
button.row label {{ font-size: {px(15)}px; font-weight: 500; }}
button.row:hover, button.row:focus {{ background: rgba(255,255,255,0.10); }}
.vline {{ background: rgba(255,255,255,0.12); min-width: 1px; }}
.dim {{ color: {DIM}; }}

/* ---------------------------------------------------------------- spotlight */
.spot-entry {{ font-size: {px(22)}px; }}
.spot-title {{ font-size: {px(15)}px; font-weight: 500; }}
.spot-sub {{ font-size: {px(12)}px; color: {DIM}; }}
button.spot-row {{ all: unset; padding: {px(8)}px {px(12)}px; border-radius: {px(10)}px; }}
button.spot-row:hover, button.spot-row.sel {{ background: rgba(255,138,31,0.28); }}

/* ---------------------------------------------------------------- control center */
.cc-title {{ font-size: {px(13)}px; font-weight: 600; }}
.cc-tile {{ all: unset; background: rgba(255,255,255,0.09); border-radius: {px(14)}px; padding: {px(10)}px {px(12)}px; }}
.cc-tile.on {{ background: linear-gradient(#ff9a2e, #ff6a10); color: #20120a; }}
.cc-tile label {{ font-size: {px(13)}px; font-weight: 600; }}
.cc-sub {{ font-size: {px(11)}px; opacity: 0.7; }}
scale.cc trough {{ background: rgba(255,255,255,0.16); border-radius: 99px; min-height: {px(8)}px; }}
scale.cc highlight {{ background: {ACC}; border-radius: 99px; }}
scale.cc slider {{ background: #fff; border-radius: 99px; min-width: {px(18)}px; min-height: {px(18)}px; box-shadow: 0 1px 4px rgba(0,0,0,0.5); }}

.toast {{ background: rgba(20,16,30,0.94); color: {TEXT}; border: 1px solid rgba(255,255,255,0.16); border-radius: 99px;
    padding: {px(10)}px {px(22)}px; font-size: {px(14)}px; font-weight: 500; box-shadow: 0 {px(8)}px {px(28)}px rgba(0,0,0,0.5); }}

/* ---------------------------------------------------------------- generic app chrome */
window.avyx-app {{ background: rgba(22,17,34,0.97); color: {TEXT}; border-radius: {px(14)}px; }}
.dim-label {{ color: {DIM}; }}
"""


_provider = None


def apply():
    global _provider
    _provider = Gtk.CssProvider()
    _provider.load_from_string(build_css())
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), _provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
    # make sure GTK itself uses a dark theme (affects scrollbars, entries ...)
    s = Gtk.Settings.get_default()
    try:
        s.set_property("gtk-application-prefer-dark-theme", True)
    except Exception:
        pass
