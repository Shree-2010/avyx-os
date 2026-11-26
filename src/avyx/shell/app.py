"""AVYX shell: wires the desktop, top bar, dock, launcher and the D-Bus control interface together."""
import os
import shlex
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gio, GLib, Gtk  # noqa: E402

from .. import apps, config, glass, theme  # noqa: E402

CTL_XML = """<node><interface name="org.avyx.Shell">
<method name="Invoke"><arg type="s" name="command" direction="in"/></method>
</interface></node>"""


class Shell:
    """Owns all shell components. `invoke()` is the single entry point for every user action."""

    def __init__(self, app):
        self.app = app
        config.Screen.init()
        theme.apply()
        glass.get()
        from .desktop import Desktop
        from .dock import Dock
        from .launcher import Launcher
        from .toast import Toast
        from .topbar import TopBar
        self.ready_written = False
        self.desktop = Desktop(self)
        self.topbar = TopBar(self)
        self.dock = Dock(self)
        self.launcher = Launcher(self)
        self.toast_win = Toast(self)
        self.extra = {}

    # ------------------------------------------------------------------ helpers
    def toast(self, text):
        self.toast_win.show(text)

    def running_ids(self):
        return set()

    def launch(self, app, extra=None):
        if app.icon is None:                        # a .desktop application from the system
            if not apps.launch_extra(app):
                self.toast("Could not start %s" % app.name)
            return
        if not app.available():
            self.toast("%s isn't installed in this build yet" % app.name)
            return
        app.launch(extra)

    def open_path(self, path):
        if path.startswith("~"):
            path = os.path.expanduser(path)
        files = apps.BY_ID["files"]
        if files.available():
            files.launch([path])
        else:
            self.toast("Files isn't installed in this build yet")

    # ------------------------------------------------------------------ command router
    def invoke(self, cmd):
        if not cmd:
            return
        name, _, arg = cmd.partition(":")
        if name == "launcher":
            self.launcher.toggle()
        elif name == "spotlight":
            self.launcher.show()
        elif name == "open":
            a = apps.BY_ID.get(arg)
            if a:
                self.launch(a)
        elif name == "quit":
            a = apps.BY_ID.get(arg)
            if a and a.running():
                a.proc.terminate()
        elif name == "path":
            self.open_path(arg)
        elif name == "cmd":
            config.spawn(shlex.split(arg))
        elif name == "settings":
            self.launch(apps.BY_ID["settings"], [arg] if arg else None)
        elif name == "lock":
            config.spawn(["avyx-lock"]) or self.toast("Lock screen isn't available yet")
        elif name == "logout":
            config.spawn(["labwc", "--exit"])
        elif name == "poweroff":
            config.spawn(["systemctl", "poweroff"])
        elif name == "reboot":
            config.spawn(["systemctl", "reboot"])
        elif name == "installer":
            config.spawn(["avyx-installer"]) or self.toast("The installer isn't available in this build")
        elif name == "about":
            self.launcher.show()
            self.launcher.select("about")
        elif name == "widgets":
            self.desktop.toggle_widgets()
        elif name == "screenshot":
            self.launch(apps.BY_ID["screenshot"])
        elif name == "files":
            self.launch(apps.BY_ID["files"])
        elif name in ("volume-up", "volume-down", "volume-mute"):
            if name == "volume-mute":
                config.spawn(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
            else:
                config.spawn(["wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", "5%+" if name == "volume-up" else "5%-"])
        elif name in ("brightness-up", "brightness-down"):
            config.spawn(["avyx-brightness", "+5" if name == "brightness-up" else "-5"])
        elif name == "toast":
            self.toast(arg)
        elif name == "restart":
            self.app.quit()
        elif name == "reload":
            self.reload()
        elif name == "testhover" and config.TEST:
            self.dock.test_hover(int(arg))
        elif name in ("cc", "overview", "window", "shortcuts"):
            self.toast("Not available yet")
        else:
            print("shell: unknown command", cmd, file=sys.stderr)

    def reload(self):
        """Re-read settings.json and apply what can change live (wallpaper needs a restart of the shell)."""
        config.settings.__init__()
        self.dock.magnify = bool(config.settings.get("magnify", True)) and self.dock.profile != "basic"
        self.desktop.wcol.set_visible(bool(config.settings.get("widgets", True)))
        if config.wallpaper_path() != getattr(glass.get(), "path", None):
            self.app.quit()          # the session wrapper restarts the shell with the new wallpaper

    # ------------------------------------------------------------------ readiness
    def on_bar_mapped(self):
        GLib.timeout_add(1500, self._write_ready)

    def _write_ready(self):
        if self.ready_written:
            return False
        self.ready_written = True
        try:
            with open("/run/avyx/shell-ready", "w") as f:
                f.write("shell")
        except OSError as e:
            print("cannot write ready marker:", e, file=sys.stderr)
        config.spawn(["avyx-mark", "shell_mapped"])
        return False


class ShellApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.avyx.Shell")
        self.shell = None

    def do_dbus_register(self, connection, object_path):
        ok = Gtk.Application.do_dbus_register(self, connection, object_path)
        try:
            info = Gio.DBusNodeInfo.new_for_xml(CTL_XML)
            connection.register_object("/org/avyx/ShellCtl", info.interfaces[0], self._method_call, None, None)
        except Exception as e:
            print("shell: could not export control interface:", e, file=sys.stderr)
        return ok

    def _method_call(self, conn, sender, path, iface, method, params, invocation):
        if method == "Invoke":
            cmd = params.unpack()[0]
            GLib.idle_add(lambda: (self.shell and self.shell.invoke(cmd), False)[1])
            invocation.return_value(None)

    def do_activate(self):
        if self.shell is None:
            self.shell = Shell(self)


def main(argv):
    return ShellApp().run(argv)
