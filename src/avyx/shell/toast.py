"""Tiny transient message at the top of the screen (used for 'not installed' and confirmations)."""
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402

from .. import config  # noqa: E402
from .util import LAYER, TOP, layer_window  # noqa: E402


class Toast:
    def __init__(self, shell):
        self.win = layer_window(shell.app, "avyx-toast", LAYER.OVERLAY, anchors=(TOP,), margins={TOP: config.px(46)}, exclusive=-1)
        self.label = Gtk.Label()
        self.label.add_css_class("toast")
        self.win.set_child(self.label)
        self._src = None

    def show(self, text, seconds=3.2):
        self.label.set_label(text)
        self.win.present()
        if self._src:
            GLib.source_remove(self._src)
        self._src = GLib.timeout_add(int(seconds * 1000), self._hide)

    def _hide(self):
        self.win.set_visible(False)
        self._src = None
        return False
