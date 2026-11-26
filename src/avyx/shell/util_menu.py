"""A small context-menu popover for any widget: items are (label, callback)."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402


class ContextMenu:
    def __init__(self, parent, items, x, y):
        self.pop = Gtk.Popover()
        self.pop.set_parent(parent)
        self.pop.set_has_arrow(False)
        self.pop.set_halign(Gtk.Align.START)
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = int(x), int(y), 1, 1
        self.pop.set_pointing_to(rect)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        for label, cb in items:
            b = Gtk.Button()
            b.add_css_class("mi")
            b.set_child(Gtk.Label(label=label, xalign=0))
            b.connect("clicked", lambda _b, c=cb: (self.pop.popdown(), c()))
            box.append(b)
        self.pop.set_child(box)
        self.pop.connect("closed", lambda p: p.unparent())
        self.pop.popup()
