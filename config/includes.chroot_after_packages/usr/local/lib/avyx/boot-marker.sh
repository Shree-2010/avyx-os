#!/bin/bash
# CI-only: prints measured boot milestones on a dedicated serial port (ttyS1). It only runs in
# the CI virtual machine, which is tagged with DMI product serial "AVYX-CI"; on real hardware
# and normal VMs this exits immediately.
[ "$(cat /sys/class/dmi/id/product_serial 2>/dev/null)" = "AVYX-CI" ] || exit 0
[ -c /dev/ttyS1 ] || exit 0
stty -F /dev/ttyS1 115200 raw -echo -crtscts -ixon 2>/dev/null
exec >/dev/ttyS1 2>&1
up() { cut -d' ' -f1 /proc/uptime; }
echo "AVYX_MARK multi_user uptime=$(up)"
echo "AVYX_MARK rootfs: $(findmnt -no SOURCE,FSTYPE / 2>/dev/null)"
echo "AVYX_MARK cmdline: $(cat /proc/cmdline)"
for i in $(seq 1 120); do
  pgrep -x plasmashell >/dev/null && break
  sleep 1
done
if pgrep -x plasmashell >/dev/null; then
  echo "AVYX_MARK plasmashell_started uptime=$(up)"
  sleep 60
  echo "AVYX_MARK desktop_idle uptime=$(up) $(awk '/MemTotal/{t=$2}/MemAvailable/{a=$2}END{printf "mem_used_mb=%d mem_total_mb=%d", (t-a)/1024, t/1024}' /proc/meminfo)"
  # Give the layout safety net time to finish (only when it is running or has logged), then report.
  for i in $(seq 1 100); do
    grep -qs "result code" /home/*/.cache/avyx-layout.log && break
    sleep 1
  done
  sleep 3
  grep -qs "result code" /home/*/.cache/avyx-layout.log && echo "AVYX_MARK layout_applied uptime=$(up)"
  echo "AVYX_MARK layout: $(cat /home/*/.cache/avyx-layout.log 2>/dev/null | tr '\n' ' ')"
  echo "== layout diagnostics =="
  ls -la /etc/xdg/autostart /usr/share/plasma/look-and-feel/org.avyx.desktop/contents /usr/share/plasma/look-and-feel/org.avyx.desktop/contents/layouts 2>&1
  for h in /home/*; do echo "--- $h"; ls -laR "$h/.config/avyx" 2>&1; ls -la "$h/.cache" 2>&1 | head -20; ls "$h/.config" 2>&1 | grep -i plasma; done
  pgrep -af "apply-layout|evaluateScript" 2>&1
  u=$(ls /home | head -1)
  echo "-- user units"; systemctl --user --machine="$u@.host" list-units --all --no-pager 2>&1 | grep -iE "avyx|autostart|plasma|graphical" | head -30
  echo "-- user journal (layout)"; journalctl -b "_UID=$(id -u "$u" 2>/dev/null)" --no-pager 2>&1 | grep -iE "avyx|layout|autostart" | tail -30
  echo "AVYX_MARK analyze: $(systemd-analyze 2>/dev/null | head -1)"
  echo "AVYX_MARK renderer: $(grep -rl llvmpipe /proc/*/environ 2>/dev/null | head -1)"
  echo "== top memory =="; ps -eo rss,comm --sort=-rss | head -12
else
  echo "AVYX_MARK plasmashell_NOT_started uptime=$(up)"
  echo "== wayland/x11 session files =="; ls -la /usr/share/wayland-sessions /usr/share/xsessions 2>&1
  echo "== sddm config =="; for f in /etc/sddm.conf /etc/sddm.conf.d/*; do [ -f "$f" ] && { echo "--- $f"; cat "$f"; }; done
  echo "== user and sessions =="; id avyx 2>&1; loginctl list-sessions --no-pager 2>&1
  echo "== session processes =="; ps -eo pid,user,args --sort=start_time | grep -E "sddm|kwin|plasma|startplasma|Xwayland" | grep -v grep | head -30
  echo "== /var/log/sddm.log =="; tail -80 /var/log/sddm.log 2>&1
  echo "== avyx user journal =="; journalctl -b "_UID=$(id -u avyx 2>/dev/null)" --no-pager 2>&1 | tail -80
echo "== sddm status =="; systemctl status sddm --no-pager 2>&1 | tail -20
  echo "== sddm journal =="; journalctl -b -u sddm --no-pager 2>&1 | tail -80
fi
echo "== errors this boot =="; journalctl -b -p err --no-pager 2>&1 | tail -60
echo "AVYX_MARK done"
