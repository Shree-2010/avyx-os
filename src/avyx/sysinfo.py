"""Small readers for CPU / memory / disk / battery / network / volume (no third-party dependencies)."""
import glob
import os
import re
import subprocess


class CpuSampler:
    def __init__(self):
        self.prev = self._read()

    @staticmethod
    def _read():
        try:
            with open("/proc/stat") as f:
                parts = f.readline().split()[1:]
            v = [int(x) for x in parts]
            idle = v[3] + (v[4] if len(v) > 4 else 0)
            return idle, sum(v)
        except (OSError, ValueError, IndexError):
            return 0, 0

    def percent(self):
        idle, total = self._read()
        di, dt = idle - self.prev[0], total - self.prev[1]
        self.prev = (idle, total)
        if dt <= 0:
            return 0.0
        return max(0.0, min(100.0, 100.0 * (1.0 - di / dt)))


def mem_percent():
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, _, rest = line.partition(":")
                info[k] = int(rest.split()[0])
        total, avail = info["MemTotal"], info.get("MemAvailable", info.get("MemFree", 0))
        return 100.0 * (total - avail) / total, total * 1024, (total - avail) * 1024
    except (OSError, KeyError, ValueError, ZeroDivisionError):
        return 0.0, 0, 0


def disk_percent(path="/"):
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        return (100.0 * (total - free) / total if total else 0.0), total, total - free
    except OSError:
        return 0.0, 0, 0


def battery():
    """(percent, charging) of the first battery, or None on machines without one."""
    for b in sorted(glob.glob("/sys/class/power_supply/BAT*")):
        try:
            with open(b + "/capacity") as f:
                cap = int(f.read().strip())
            try:
                with open(b + "/status") as f:
                    st = f.read().strip()
            except OSError:
                st = ""
            return cap, st in ("Charging", "Full")
        except (OSError, ValueError):
            continue
    return None


def network_kind():
    """'wifi' | 'ethernet' | 'none' by looking at link state."""
    best = "none"
    for n in glob.glob("/sys/class/net/*"):
        name = os.path.basename(n)
        if name == "lo" or name.startswith(("veth", "docker", "virbr", "br-")):
            continue
        try:
            with open(n + "/operstate") as f:
                state = f.read().strip()
        except OSError:
            continue
        if state != "up":
            continue
        if os.path.isdir(n + "/wireless") or os.path.isdir(n + "/phy80211"):
            return "wifi"
        best = "ethernet"
    return best


def has_wifi_hw():
    return any(os.path.isdir(n + "/wireless") or os.path.isdir(n + "/phy80211") for n in glob.glob("/sys/class/net/*"))


def has_bluetooth_hw():
    return bool(glob.glob("/sys/class/bluetooth/hci*"))


def volume():
    """(level 0..1, muted) from WirePlumber, or None. Blocking (spawns wpctl) - call from a thread."""
    try:
        out = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True, timeout=2).stdout
        m = re.search(r"([0-9.]+)", out)
        if not m:
            return None
        return float(m.group(1)), "MUTED" in out
    except (OSError, subprocess.SubprocessError):
        return None


def set_volume(level):
    try:
        subprocess.run(["wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", "%.2f" % level], timeout=2)
    except (OSError, subprocess.SubprocessError):
        pass


def toggle_mute():
    try:
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], timeout=2)
    except (OSError, subprocess.SubprocessError):
        pass


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return ("%.0f %s" if unit in ("B", "KB", "MB") else "%.1f %s") % (n, unit)
        n /= 1024.0
