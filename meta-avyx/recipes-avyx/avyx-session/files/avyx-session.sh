# Start the AVYX desktop on the first virtual terminal for normal users.
if [ -z "$WAYLAND_DISPLAY" ] && [ "$(id -u)" != 0 ] && [ "$(tty 2>/dev/null)" = "/dev/tty1" ]; then
    exec /usr/bin/avyx-session
fi
