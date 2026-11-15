#!/bin/bash
# CI-only: start the Calamares installer automatically, and report on the CI serial port (ttyS1).
# Does nothing unless the virtual machine's DMI product family is AVYX-CI-INSTALL.
[ "$(cat /sys/class/dmi/id/product_family 2>/dev/null)" = "AVYX-CI-INSTALL" ] || exit 0
sleep 6
exec sudo -E bash -c '
  exec >/dev/ttyS1 2>&1
  echo "AVYX_MARK calamares_launch"
  calamares -d
  rc=$?
  echo "AVYX_MARK calamares_exit rc=$rc"
  tail -n 300 /root/.cache/calamares/session.log 2>/dev/null
  echo "AVYX_MARK install_log_done"
'
