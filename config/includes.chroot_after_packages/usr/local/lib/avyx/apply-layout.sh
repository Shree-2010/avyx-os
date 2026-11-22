#!/bin/bash
# Apply the AVYX panel layout once per user, as soon as plasmashell is reachable on D-Bus.
# Normally Plasma already built the layout from the AVYX look-and-feel package on its first start;
# this is the safety net. It can be started from two places (XDG autostart and a systemd user
# unit), so it takes a lock and checks what is already on screen before touching anything.
[ "$(id -u)" -ge 1000 ] || exit 0
marker="$HOME/.config/avyx/layout-applied-v1"
log="$HOME/.cache/avyx-layout.log"
[ -e "$marker" ] && exit 0
mkdir -p "$(dirname "$marker")" "$(dirname "$log")"
exec 9>"$HOME/.cache/avyx-layout.lock"
flock -n 9 || exit 0
[ -e "$marker" ] && exit 0
exec >>"$log" 2>&1
echo "start $(date +%T) via=${1:-autostart} bus=${DBUS_SESSION_BUS_ADDRESS:-unset} wayland=${WAYLAND_DISPLAY:-unset}"
ok=0
for i in $(seq 1 120); do
  gdbus call --session --dest org.kde.plasmashell --object-path /PlasmaShell \
    --method org.freedesktop.DBus.Peer.Ping >/dev/null 2>&1 && { ok=1; break; }
  sleep 1
done
echo "plasmashell reachable=$ok after ${i}s"
sleep 4
state=$(gdbus call --session --dest org.kde.plasmashell --object-path /PlasmaShell \
  --method org.kde.PlasmaShell.evaluateScript \
  'var o=[];for(var i=0;i<panels().length;i++){o.push(panels()[i].location)};print(o.join(","))' 2>&1)
echo "panels now: $state"
# Frosted glass: translucent panels. Done here too because it does not depend on how the panels
# were created; harmless if this Plasma version has no such property.
glassmark="$HOME/.config/avyx/glass-applied-v1"
if [ ! -e "$glassmark" ]; then
  gdbus call --session --dest org.kde.plasmashell --object-path /PlasmaShell \
    --method org.kde.PlasmaShell.evaluateScript \
    'var n=0;for(var i=0;i<panels().length;i++){try{panels()[i].opacity="translucent";n++}catch(e){}};print("glass:"+n)' 2>&1
  touch "$glassmark"
fi
case "$state" in
  *top*bottom*|*bottom*top*)
    echo "layout already present (built by the look-and-feel package)"
    echo "result code: 0"
    touch "$marker"; exit 0 ;;
esac
echo "applying layout at $(date +%T)"
gdbus call --session --dest org.kde.plasmashell --object-path /PlasmaShell \
  --method org.kde.PlasmaShell.evaluateScript "$(cat /usr/share/avyx/layout.js)" 2>&1
rc=$?
echo "result code: $rc"
[ $rc -eq 0 ] && touch "$marker"
