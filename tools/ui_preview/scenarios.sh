# sourced by run.sh after the first screenshot; $OUT, shot() and PATH (with avyx-ctl) are available
ctl() { avyx-ctl "$1" >>"$OUT/ctl.log" 2>&1 || echo "ctl $1 failed" >>"$OUT/ctl.log"; sleep "${2:-1.2}"; }

ctl testhover:3 1.5
shot 02-dock-hover
ctl testhover:-1 1

ctl launcher 1.8
shot 03-launcher
ctl about 1.2
shot 04-launcher-about
ctl launcher 0.8

ctl files 1
shot 05-files-missing-toast
