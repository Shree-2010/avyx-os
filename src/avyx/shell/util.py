"""Helpers for layer-shell windows and popover menus."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk  # noqa: E402
from gi.repository import Gtk4LayerShell as LS  # noqa: E402

from .. import config  # noqa: E402

E = LS.Edge
TOP, BOTTOM, LEFT, RIGHT = E.TOP, E.BOTTOM, E.LEFT, E.RIGHT


def layer_window(app, namespace, layer, anchors=(), margins=None, exclusive=0, keyboard=None, size=None):
    """Create a Gtk.Window that is a wlr-layer-shell surface. Records its screen position in `_origin`."""
    win = Gtk.Window(application=app)
    win.set_decorated(False)
    win.set_resizable(False)
    win.add_css_class("avyx-layer")
    LS.init_for_window(win)
    LS.set_namespace(win, namespace)
    LS.set_layer(win, layer)
    for e in (TOP, BOTTOM, LEFT, RIGHT):
        LS.set_anchor(win, e, e in anchors)
    for e, v in (margins or {}).items():
        LS.set_margin(win, e, int(v))
    if exclusive == "auto":
        LS.auto_exclusive_zone_enable(win)
    else:
        LS.set_exclusive_zone(win, exclusive)
    LS.set_keyboard_mode(win, keyboard if keyboard is not None else LS.KeyboardMode.NONE)
    if size:
        win.set_default_size(*size)
    win._origin = (0, 0)
    return win


LAYER = LS.Layer
KB = LS.KeyboardMode


def set_origin(win, x, y):
    win._origin = (int(x), int(y))


class Menu:
    """A popover with menu items. items: (label, command, shortcut) tuples or '-' separators."""

    def __init__(self, shell, anchor, items):
        self.shell = shell
        self.pop = Gtk.Popover()
        self.pop.set_parent(anchor)
        self.pop.set_has_arrow(False)
        self.pop.set_position(Gtk.PositionType.BOTTOM)
        self.pop.set_halign(Gtk.Align.START)
        self.pop.add_css_class("avyx-pop")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        for it in items:
            if it == "-":
                sep = Gtk.Separator()
                sep.add_css_class("mi")
                box.append(sep)
                continue
            label, cmd, key = (list(it) + [None, None])[:3]
            b = Gtk.Button()
            b.add_css_class("mi")
            row = Gtk.Box(spacing=config.px(24))
            lab = Gtk.Label(label=label, xalign=0, hexpand=True)
            row.append(lab)
            if key:
                kl = Gtk.Label(label=key)
                kl.add_css_class("key")
                row.append(kl)
            b.set_child(row)
            b.connect("clicked", lambda _b, c=cmd: (self.pop.popdown(), shell.invoke(c) if c else None))
            box.append(b)
        self.pop.set_child(box)

    def popup(self):
        self.pop.popup()
