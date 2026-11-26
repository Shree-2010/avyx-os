"""Current weather from Open-Meteo (no API key). Only used when the user has set a location."""
import json
import threading
import urllib.request

from gi.repository import GLib

CODES = {
    0: ("Clear", "sun"), 1: ("Mostly Clear", "sun"), 2: ("Partly Cloudy", "cloud-sun"), 3: ("Overcast", "cloud"),
    45: ("Fog", "cloud"), 48: ("Fog", "cloud"), 51: ("Drizzle", "rain"), 53: ("Drizzle", "rain"), 55: ("Drizzle", "rain"),
    61: ("Rain", "rain"), 63: ("Rain", "rain"), 65: ("Heavy Rain", "rain"), 71: ("Snow", "cloud"), 73: ("Snow", "cloud"),
    75: ("Snow", "cloud"), 80: ("Showers", "rain"), 81: ("Showers", "rain"), 82: ("Heavy Showers", "rain"),
    95: ("Thunderstorm", "rain"), 96: ("Thunderstorm", "rain"), 99: ("Thunderstorm", "rain"),
}


def fetch(lat, lon, callback):
    """callback(temp_c, text, kind) is invoked on the GLib main loop; nothing happens when offline."""
    def work():
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&current_weather=true" % (lat, lon)
            with urllib.request.urlopen(url, timeout=8) as r:
                cur = json.load(r)["current_weather"]
            text, kind = CODES.get(int(cur.get("weathercode", 3)), ("", "cloud"))
            GLib.idle_add(callback, float(cur["temperature"]), text, kind)
        except Exception:
            pass
    threading.Thread(target=work, daemon=True).start()
