#!/bin/bash
# Prints measured boot milestones on the serial console. Only runs when the kernel
# command line asks for a serial console (CI); on real hardware it is a no-op.
[ -c /dev/ttyS0 ] || exit 0
exec >/dev/ttyS0 2>&1
up() { cut -d' ' -f1 /proc/uptime; }
echo "AVYX_MARK multi_user uptime=$(up)"
for i in $(seq 1 1200); do
  pgrep -x plasmashell >/dev/null && break
  sleep 1
done
if pgrep -x plasmashell >/dev/null; then
  echo "AVYX_MARK plasmashell_started uptime=$(up)"
  sleep 60
  echo "AVYX_MARK desktop_idle uptime=$(up) $(awk '/MemTotal/{t=$2}/MemAvailable/{a=$2}END{printf "mem_used_mb=%d mem_total_mb=%d", (t-a)/1024, t/1024}' /proc/meminfo)"
  echo "AVYX_MARK analyze: $(systemd-analyze 2>/dev/null | head -1)"
  echo "AVYX_MARK renderer: $(grep -rl llvmpipe /proc/*/environ 2>/dev/null | head -1)"
  echo "== top memory =="; ps -eo rss,comm --sort=-rss | head -12
else
  echo "AVYX_MARK plasmashell_NOT_started uptime=$(up)"
  echo "== sddm status =="; systemctl status sddm --no-pager 2>&1 | tail -20
  echo "== sddm journal =="; journalctl -b -u sddm --no-pager 2>&1 | tail -40
fi
echo "== errors this boot =="; journalctl -b -p err --no-pager 2>&1 | tail -60
echo "AVYX_MARK done"
