#!/bin/sh
# Live-session-only setup. Runs from avyx-live-session.service when booted with boot=live.
# It lives outside the squashfs overlay, so none of this is carried into an installed system.
set -e

sess=""
for s in plasma.desktop plasmawayland.desktop; do
  if [ -f "/usr/share/wayland-sessions/$s" ]; then sess="$s"; break; fi
done
sess="${sess:-plasma.desktop}"

mkdir -p /etc/sddm.conf.d
cat > /etc/sddm.conf.d/zz-avyx-live-autologin.conf <<CONF
[Autologin]
User=avyx
Session=${sess}
Relogin=false
CONF

home="$(getent passwd avyx | cut -d: -f6)"
if [ -n "$home" ] && [ -d "$home" ]; then
  mkdir -p "$home/Desktop"
  cp /usr/share/applications/avyx-installer.desktop "$home/Desktop/"
  chmod +x "$home/Desktop/avyx-installer.desktop"
  chown -R avyx:avyx "$home/Desktop"
fi
echo "avyx-live-session: autologin session=$sess"
