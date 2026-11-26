"""AVYX Files: a small, fast file manager (grid/list views, sidebar, search, trash)."""
import os
import shutil
import sys
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk  # noqa: E402

from .. import appkit, apps, config, sysinfo  # noqa: E402
from ..appkit import AppWindow, icon_button  # noqa: E402
from ..gfx import Glyph  # noqa: E402

px = config.px
HOME = os.path.expanduser("~")
TRASH = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.join(HOME, ".local/share")), "Trash", "files")
TRASH_URI = "trash:///"
COMPUTER_URI = "computer:///"

SIDEBAR = [("Home", "home-fill", HOME), ("Desktop", "window", os.path.join(HOME, "Desktop")), ("Documents", "doc", os.path.join(HOME, "Documents")),
           ("Downloads", "download", os.path.join(HOME, "Downloads")), ("Music", "music", os.path.join(HOME, "Music")),
           ("Pictures", "picture", os.path.join(HOME, "Pictures")), ("Videos", "video", os.path.join(HOME, "Videos")), ("Trash", "trash", TRASH_URI)]
FOLDER_ICONS = {"Desktop": "folder", "Documents": "folder-documents", "Downloads": "folder-downloads", "Music": "folder-music",
                "Pictures": "folder-pictures", "Videos": "folder-videos", "Projects": "folder-projects"}
EXT = {
    "file-image": "png jpg jpeg gif webp bmp svg tif tiff ico",
    "file-audio": "mp3 flac ogg oga wav m4a opus aac wma",
    "file-video": "mp4 mkv webm avi mov m4v mpg mpeg wmv flv",
    "file-archive": "zip tar gz tgz xz bz2 zst 7z rar iso",
    "file-code": "py c h cpp hpp js ts json html htm css sh bash xml yml yaml toml rs go java lua",
    "file-text": "txt md log cfg conf ini csv rst tex",
}
EXT_ICON = {e: icon for icon, exts in EXT.items() for e in exts.split()}
OPENERS = {"file-image": ["avyx-photos"], "file-audio": ["avyx-media"], "file-video": ["avyx-media"], "file-code": ["avyx-editor"], "file-text": ["avyx-editor"]}


class Entry:
    def __init__(self, name, path, is_dir, size=0, mtime=0, icon=None, trash=False):
        self.name, self.path, self.is_dir, self.size, self.mtime = name, path, is_dir, size, mtime
        self.trash = trash
        self.icon = icon or self._icon()

    def _icon(self):
        if self.is_dir:
            if os.path.dirname(self.path) == HOME:
                return FOLDER_ICONS.get(self.name, "folder")
            return "folder"
        return EXT_ICON.get(self.name.rsplit(".", 1)[-1].lower() if "." in self.name else "", "file")


def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return ("%d %s" if u == "B" else "%.1f %s") % (n, u)
        n /= 1024.0


class FilesWindow(AppWindow):
    def __init__(self, app, path):
        super().__init__(app, "Files", 1000, 640)
        self.history, self.fwd = [], []
        self.path = None
        self.view = "grid"
        self.hidden = False
        self.filter = ""
        self.entries = []
        self.monitor = None
        self._mon_src = None
        self._thumb_src = None

        # ---- header
        self.back_b = icon_button("chev-l", "Back", self.go_back)
        self.fwd_b = icon_button("chev-r", "Forward", self.go_forward)
        self.header_append(self.back_b)
        self.header_append(self.fwd_b)
        self.title = Gtk.Label(xalign=0, hexpand=True)
        self.title.add_css_class("app-title")
        self.title.set_margin_start(px(8))
        self.header_append(self.title)
        self.grid_b = icon_button("grid", "Icons", lambda: self.set_view("grid"))
        self.list_b = icon_button("list", "List", lambda: self.set_view("list"))
        self.header_append(self.grid_b)
        self.header_append(self.list_b)
        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("Search")
        self.search.add_css_class("field")
        self.search.set_size_request(px(190), -1)
        self.search.connect("search-changed", self._search_changed)
        self.header_append(self.search)
        self.new_b = icon_button("plus", "New Folder", self.new_folder)
        self.header_append(self.new_b)

        # ---- body
        main = Gtk.Box()
        main.set_vexpand(True)
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(2))
        side.add_css_class("files-side")
        side.set_size_request(px(200), -1)
        self.side_btns = {}
        for name, glyph, target in SIDEBAR:
            b = Gtk.Button()
            b.add_css_class("side")
            row = Gtk.Box(spacing=px(11))
            row.append(Glyph(glyph, px(18)))
            row.append(Gtk.Label(label=name, xalign=0))
            b.set_child(row)
            b.connect("clicked", lambda _b, t=target: self.navigate(t))
            side.append(b)
            self.side_btns[target] = b
        side.append(Gtk.Box(vexpand=True))
        dev = Gtk.Button()
        dev.add_css_class("side")
        r = Gtk.Box(spacing=px(11))
        r.append(Glyph("window", px(18)))
        r.append(Gtk.Label(label="This PC", xalign=0))
        dev.set_child(r)
        dev.connect("clicked", lambda *_: self.navigate(COMPUTER_URI))
        side.append(dev)
        self.side_btns[COMPUTER_URI] = dev
        main.append(side)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_vexpand(True)
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        right.append(self.scroll)
        self.status = Gtk.Label(xalign=0)
        self.status.add_css_class("status-bar")
        self.trash_bar = Gtk.Box(spacing=px(8))
        self.empty_b = Gtk.Button(label="Empty Trash")
        self.empty_b.add_css_class("btn")
        self.empty_b.connect("clicked", lambda *_: self.empty_trash())
        self.trash_bar.set_margin_start(px(14))
        self.trash_bar.set_margin_bottom(px(6))
        self.trash_bar.append(self.empty_b)
        right.append(self.trash_bar)
        right.append(self.status)
        main.append(right)
        self.body.append(main)

        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self._key)
        self.add_controller(key)
        self.navigate(path or HOME, push=False)

    # ------------------------------------------------------------------ navigation
    def navigate(self, path, push=True):
        if path.startswith("~"):
            path = os.path.expanduser(path)
        if path not in (TRASH_URI, COMPUTER_URI):
            path = os.path.abspath(path)
            if not os.path.isdir(path):
                appkit.message(self, "Folder not found", path)
                return
        if push and self.path and self.path != path:
            self.history.append(self.path)
            self.fwd.clear()
        self.path = path
        self.search.set_text("")
        self.filter = ""
        self.refresh()
        self._watch()

    def go_back(self):
        if self.history:
            self.fwd.append(self.path)
            self.navigate(self.history.pop(), push=False)

    def go_forward(self):
        if self.fwd:
            self.history.append(self.path)
            self.navigate(self.fwd.pop(), push=False)

    def go_up(self):
        if self.path and self.path not in (TRASH_URI, COMPUTER_URI) and self.path != "/":
            self.navigate(os.path.dirname(self.path))

    def set_view(self, v):
        self.view = v
        self.render()

    # ------------------------------------------------------------------ data
    def _is_trash(self):
        return self.path == TRASH_URI

    def refresh(self):
        self.entries = []
        if self.path == COMPUTER_URI:
            self.entries = self._computer()
            self.title.set_label("This PC")
        else:
            real = TRASH if self._is_trash() else self.path
            try:
                os.makedirs(real, exist_ok=True) if self._is_trash() else None
                with os.scandir(real) as it:
                    for e in it:
                        try:
                            st = e.stat(follow_symlinks=False)
                            is_dir = e.is_dir(follow_symlinks=True)
                        except OSError:
                            continue
                        self.entries.append(Entry(e.name, e.path, is_dir, st.st_size, st.st_mtime, trash=self._is_trash()))
            except OSError as ex:
                self.entries = []
                self.status.set_label("Cannot read this folder: %s" % ex.strerror)
            self.entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))
            self.title.set_label("Trash" if self._is_trash() else (os.path.basename(self.path.rstrip("/")) or "/") if self.path != HOME else "Home")
        self.render()
        self.back_b.set_sensitive(bool(self.history))
        self.fwd_b.set_sensitive(bool(self.fwd))
        self.new_b.set_visible(self.path not in (TRASH_URI, COMPUTER_URI))
        self.trash_bar.set_visible(self._is_trash())
        for t, b in self.side_btns.items():
            (b.add_css_class if t == self.path else b.remove_css_class)("sel")
        self.set_title("%s — Files" % self.title.get_label())

    def _computer(self):
        out = []
        pct, total, used = sysinfo.disk_percent("/")
        out.append(Entry("AVYX OS (%s free)" % human(total - used), "/", True, icon="this-pc"))
        try:
            with open("/proc/mounts") as f:
                for line in f:
                    dev, mnt = line.split()[:2]
                    if mnt.startswith(("/media/", "/run/media/", "/mnt/")) and dev.startswith("/dev/"):
                        out.append(Entry(os.path.basename(mnt), mnt, True, icon="this-pc"))
        except OSError:
            pass
        return out

    def _visible(self):
        q = self.filter.lower()
        return [e for e in self.entries if (self.hidden or not e.name.startswith(".")) and (not q or q in e.name.lower())]

    # ------------------------------------------------------------------ rendering
    def render(self):
        items = self._visible()
        if self._thumb_src:
            GLib.source_remove(self._thumb_src)
            self._thumb_src = None
        for b, v in ((self.grid_b, "grid"), (self.list_b, "list")):
            (b.add_css_class if self.view == v else b.remove_css_class)("on")
        if not items:
            lab = Gtk.Label(label="Trash is empty" if self._is_trash() else ("No matches" if self.filter else "This folder is empty"))
            lab.add_css_class("empty-note")
            lab.set_vexpand(True)
            self.scroll.set_child(lab)
            self.status.set_label("0 items")
            return
        self.pending_thumbs = []
        if self.view == "grid":
            fb = Gtk.FlowBox()
            fb.add_css_class("items")
            fb.set_valign(Gtk.Align.START)
            fb.set_selection_mode(Gtk.SelectionMode.SINGLE)
            fb.set_activate_on_single_click(False)
            fb.set_min_children_per_line(2)
            fb.set_max_children_per_line(30)
            fb.set_homogeneous(True)
            fb.set_row_spacing(px(6))
            fb.set_column_spacing(px(6))
            for e in items:
                fb.append(self._grid_item(e))
            fb.connect("child-activated", lambda _f, c: self.open_entry(c.entry))
            self.container = fb
            self.scroll.set_child(fb)
        else:
            lb = Gtk.ListBox()
            lb.add_css_class("items")
            lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
            lb.set_activate_on_single_click(False)
            for e in items:
                lb.append(self._list_row(e))
            lb.connect("row-activated", lambda _l, r: self.open_entry(r.entry))
            self.container = lb
            self.scroll.set_child(lb)
        n = len(items)
        self.status.set_label("%d item%s" % (n, "" if n == 1 else "s"))
        if self.pending_thumbs:
            self._thumb_src = GLib.idle_add(self._thumb_step)

    def _attach_menu(self, widget, entry):
        g = Gtk.GestureClick()
        g.set_button(3)
        g.connect("pressed", lambda gg, n, x, y: self._context(widget, entry, x, y))
        widget.add_controller(g)
        widget.entry = entry

    def _grid_item(self, e):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=px(6))
        box.set_size_request(px(112), -1)
        pic = apps.icon_widget(e.icon, px(76))
        pic.set_margin_top(px(4))
        box.append(pic)
        lab = Gtk.Label(label=e.name)
        lab.set_ellipsize(3)
        lab.set_max_width_chars(14)
        lab.set_lines(2)
        lab.set_wrap(True)
        lab.set_justify(Gtk.Justification.CENTER)
        box.append(lab)
        if e.icon == "file-image" and e.size < 12 * 1024 * 1024:
            self.pending_thumbs.append((e, box, pic))
        child = Gtk.FlowBoxChild()
        child.set_child(box)
        self._attach_menu(child, e)
        return child

    def _list_row(self, e):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(spacing=px(12))
        box.append(apps.icon_widget(e.icon, px(28)))
        n = Gtk.Label(label=e.name, xalign=0, hexpand=True)
        n.set_ellipsize(3)
        box.append(n)
        sz = Gtk.Label(label="" if e.is_dir else human(e.size), xalign=1)
        sz.add_css_class("dim-label")
        sz.set_size_request(px(80), -1)
        box.append(sz)
        mt = Gtk.Label(label=time.strftime("%b %-d, %Y  %-I:%M %p", time.localtime(e.mtime)) if e.mtime else "", xalign=1)
        mt.add_css_class("dim-label")
        mt.set_size_request(px(170), -1)
        box.append(mt)
        row.set_child(box)
        self._attach_menu(row, e)
        return row

    def _thumb_step(self):
        for _ in range(3):
            if not self.pending_thumbs:
                self._thumb_src = None
                return False
            e, box, pic = self.pending_thumbs.pop(0)
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(e.path, px(152), px(152), True)
                pic.set_paintable(Gdk.Texture.new_for_pixbuf(pb))
                pic.set_size_request(px(76), px(76))
            except GLib.Error:
                pass
        return True

    # ------------------------------------------------------------------ actions
    def open_entry(self, e):
        if e.trash:
            return
        if e.is_dir:
            self.navigate(e.path)
            return
        ext = e.name.rsplit(".", 1)[-1].lower() if "." in e.name else ""
        cmd = OPENERS.get(EXT_ICON.get(ext, ""))
        if cmd and config.spawn(cmd + [e.path]):
            return
        try:
            Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(e.path).get_uri(), None)
        except GLib.Error:
            appkit.message(self, "No app to open this file", "Install an app that can open “%s”." % e.name)

    def _context(self, widget, e, x, y):
        from ..shell.util_menu import ContextMenu
        items = []
        if e.trash:
            items = [("Restore", lambda: self.restore(e)), ("Delete Permanently", lambda: self.delete_forever(e))]
        elif self.path == COMPUTER_URI:
            items = [("Open", lambda: self.open_entry(e))]
        else:
            items = [("Open", lambda: self.open_entry(e)), ("Rename…", lambda: self.rename(e)), ("Move to Trash", lambda: self.trash(e)),
                     ("Copy Path", lambda: self.copy_path(e))]
        ContextMenu(widget, items, x, y)

    def new_folder(self):
        def make(name):
            try:
                os.mkdir(os.path.join(self.path, name))
            except OSError as ex:
                appkit.message(self, "Could not create folder", ex.strerror or str(ex))
            self.refresh()
        appkit.prompt(self, "New Folder", "untitled folder", "Create", make)

    def rename(self, e):
        def do(name):
            try:
                os.rename(e.path, os.path.join(os.path.dirname(e.path), name))
            except OSError as ex:
                appkit.message(self, "Could not rename", ex.strerror or str(ex))
            self.refresh()
        appkit.prompt(self, "Rename", e.name, "Rename", do)

    def trash(self, e):
        try:
            Gio.File.new_for_path(e.path).trash(None)
        except GLib.Error as ex:
            appkit.message(self, "Could not move to Trash", ex.message)
        self.refresh()

    def restore(self, e):
        info = os.path.join(os.path.dirname(os.path.dirname(e.path)), "info", e.name + ".trashinfo")
        dest = os.path.join(HOME, e.name)
        try:
            with open(info) as f:
                for line in f:
                    if line.startswith("Path="):
                        from urllib.parse import unquote
                        dest = unquote(line.split("=", 1)[1].strip())
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(e.path, dest)
            os.remove(info)
        except OSError as ex:
            appkit.message(self, "Could not restore", ex.strerror or str(ex))
        self.refresh()

    def _rm(self, e):
        try:
            if e.is_dir and not os.path.islink(e.path):
                shutil.rmtree(e.path)
            else:
                os.remove(e.path)
            info = os.path.join(os.path.dirname(os.path.dirname(e.path)), "info", e.name + ".trashinfo")
            if os.path.exists(info):
                os.remove(info)
        except OSError:
            pass

    def delete_forever(self, e):
        appkit.confirm(self, "Delete “%s” permanently?" % e.name, "This cannot be undone.", "Delete", lambda: (self._rm(e), self.refresh()))

    def empty_trash(self):
        def go():
            for e in list(self.entries):
                self._rm(e)
            self.refresh()
        appkit.confirm(self, "Empty the Trash?", "All items in the Trash will be deleted permanently.", "Empty Trash", go)

    def copy_path(self, e):
        self.get_clipboard().set(e.path)

    # ------------------------------------------------------------------ misc
    def _search_changed(self, entry):
        self.filter = entry.get_text()
        self.render()

    def _key(self, ctl, keyval, keycode, state):
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        alt = bool(state & Gdk.ModifierType.ALT_MASK)
        if keyval == Gdk.KEY_BackSpace and not self.search.has_focus():
            self.go_up()
            return True
        if alt and keyval == Gdk.KEY_Left:
            self.go_back()
            return True
        if alt and keyval == Gdk.KEY_Right:
            self.go_forward()
            return True
        if ctrl and keyval in (Gdk.KEY_h, Gdk.KEY_H):
            self.hidden = not self.hidden
            self.render()
            return True
        if ctrl and keyval in (Gdk.KEY_f, Gdk.KEY_F):
            self.search.grab_focus()
            return True
        if ctrl and keyval in (Gdk.KEY_n, Gdk.KEY_N) and state & Gdk.ModifierType.SHIFT_MASK:
            self.new_folder()
            return True
        if ctrl and keyval in (Gdk.KEY_n, Gdk.KEY_N):
            self.get_application().activate()
            return True
        if ctrl and keyval in (Gdk.KEY_w, Gdk.KEY_W):
            self.close()
            return True
        return False

    def _watch(self):
        if self.monitor:
            self.monitor.cancel()
            self.monitor = None
        real = TRASH if self._is_trash() else self.path
        if real in (COMPUTER_URI,) or not os.path.isdir(real):
            return
        try:
            self.monitor = Gio.File.new_for_path(real).monitor_directory(Gio.FileMonitorFlags.NONE, None)
            self.monitor.connect("changed", self._changed)
        except GLib.Error:
            self.monitor = None

    def _changed(self, *_):
        if self._mon_src is None:
            self._mon_src = GLib.timeout_add(250, self._mon_refresh)

    def _mon_refresh(self):
        self._mon_src = None
        self.refresh()
        return False


class FilesApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.avyx.Files", flags=Gio.ApplicationFlags.HANDLES_OPEN)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        appkit.setup_env()

    def do_activate(self):
        FilesWindow(self, HOME).present()

    def do_open(self, files, n, hint):
        for f in files:
            p = f.get_path() or f.get_uri()
            if p and p.startswith("trash:"):
                p = TRASH_URI
            elif p and p.startswith("computer:"):
                p = COMPUTER_URI
            FilesWindow(self, p).present()


def main(argv):
    # accept plain paths and the pseudo-URIs used by the shell (trash:///, computer:///)
    args = [argv[0]]
    for a in argv[1:]:
        if a.startswith(("trash:", "computer:")) or "://" in a:
            args.append(a)
        else:
            args.append(Gio.File.new_for_commandline_arg(a).get_uri())
    return FilesApp().run(args)
