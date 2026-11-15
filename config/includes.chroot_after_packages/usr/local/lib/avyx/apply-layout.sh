#!/bin/bash
# Apply the AVYX panel layout once per user, as soon as plasmashell is reachable on D-Bus.
marker="$HOME/.config/avyx/layout-applied-v1"
log="$HOME/.cache/avyx-layout.log"
[ -e "$marker" ] && exit 0
mkdir -p "$(dirname "$marker")" "$(dirname "$log")"
{
  for i in $(seq 1 90); do
    gdbus call --session --dest org.kde.plasmashell --object-path /PlasmaShell \
      --method org.freedesktop.DBus.Peer.Ping >/dev/null 2>&1 && break
    sleep 1
  done
  sleep 4
  echo "applying layout at $(date +%T)"
  gdbus call --session --dest org.kde.plasmashell --object-path /PlasmaShell \
    --method org.kde.PlasmaShell.evaluateScript "$(cat /usr/share/avyx/layout.js)" 2>&1
  echo "result code: $?"
} >> "$log" 2>&1
touch "$marker"
