#!/usr/bin/env bash
# Usage (inside a D-Bus session): run.sh OUTDIR
# Starts labwc headless at 1536x1024, runs the AVYX shell from the source tree, takes screenshots.
set -u
OUT="$(realpath "$1")"; mkdir -p "$OUT"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export XDG_RUNTIME_DIR="$(mktemp -d)"; chmod 700 "$XDG_RUNTIME_DIR"
export WLR_BACKENDS=headless WLR_LIBINPUT_NO_DEVICES=1 WLR_RENDERER=pixman
export GDK_BACKEND=wayland GSK_RENDERER=cairo
export PYTHONPATH="$ROOT/src" AVYX_DATA="$ROOT/src/data/share/avyx" AVYX_TEST=1 PYTHONUNBUFFERED=1
export XDG_DATA_DIRS="$ROOT/src/data/share:/usr/local/share:/usr/share"
export PATH="$ROOT/src/bin:$ROOT/src/native:$PATH"
CFG="$(mktemp -d)"; cp "$ROOT"/meta-avyx/recipes-avyx/avyx-session/files/labwc/rc.xml "$CFG/"
mkdir -p "$XDG_RUNTIME_DIR" /tmp/avyxrun 2>/dev/null

labwc -C "$CFG" >"$OUT/labwc.log" 2>&1 &
LPID=$!
for i in $(seq 1 50); do ls "$XDG_RUNTIME_DIR"/wayland-* >/dev/null 2>&1 && break; sleep 0.2; done
export WAYLAND_DISPLAY="$(basename "$(ls "$XDG_RUNTIME_DIR"/wayland-* | grep -v lock | head -1)")"
echo "wayland display: $WAYLAND_DISPLAY"
wlr-randr --output HEADLESS-1 --custom-mode 1536x1024 >"$OUT/randr.log" 2>&1 || wlr-randr >>"$OUT/randr.log" 2>&1
sleep 1

python3 "$ROOT/src/bin/avyx-shell" >"$OUT/shell.log" 2>&1 &
SPID=$!
sleep 6
shot() { grim "$OUT/$1.png" 2>>"$OUT/grim.log"; echo "shot $1"; }
shot 01-desktop

# scenarios file (optional, grows over time)
if [ -f "$ROOT/tools/ui_preview/scenarios.sh" ]; then
    # shellcheck disable=SC1090
    source "$ROOT/tools/ui_preview/scenarios.sh"
fi

kill $SPID 2>/dev/null; sleep 0.5; kill $LPID 2>/dev/null
cat "$OUT/shell.log" | tail -30
exit 0
