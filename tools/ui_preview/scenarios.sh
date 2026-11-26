# sourced by run.sh after the first screenshot; $OUT, $ROOT, shot() and PATH (with avyx-ctl) are available
ctl() { avyx-ctl "$1" >>"$OUT/ctl.log" 2>&1 || echo "ctl $1 failed" >>"$OUT/ctl.log"; sleep "${2:-1.2}"; }

ctl testhover:3 1.5
shot 02-dock-hover
ctl testhover:-1 1

ctl launcher 1.8
shot 03-launcher
ctl about 1.2
shot 04-launcher-about
ctl launcher 0.8

# ---- apps (run directly so their stderr is captured), with a demo home directory
DEMO="$(mktemp -d)"
mkdir -p "$DEMO"/{Desktop,Documents,Downloads,Music,Pictures,Videos,Projects,.config}
printf 'Hello from AVYX OS\nBuild beyond limits.\n' > "$DEMO/Documents/notes.txt"
printf 'print("hi")\n' > "$DEMO/Projects/app.py"
cp "$ROOT/src/data/share/avyx/wallpapers/default.jpg" "$DEMO/Pictures/sunset.jpg"
cp "$ROOT/src/data/share/avyx/wallpapers/default.jpg" "$DEMO/Pictures/bridge.jpg"
head -c 1048576 /dev/urandom > "$DEMO/Downloads/archive.zip"
echo x > "$DEMO/Music/song.mp3"; echo x > "$DEMO/Videos/clip.mp4"
export APPHOME="$DEMO"
app() {   # app NAME COMMAND...
    local name="$1"; shift
    HOME="$DEMO" XDG_CONFIG_HOME="$DEMO/.config" "$@" >"$OUT/app-$name.log" 2>&1 &
    local pid=$!
    sleep "${WAIT:-5}"
    shot "$name"
    kill $pid 2>/dev/null; sleep 1
}
app 10-files avyx-files
app 11-settings-network avyx-settings network
app 12-settings-display avyx-settings display
app 13-settings-appearance avyx-settings appearance
app 14-settings-about avyx-settings about
app 15-calculator avyx-calculator
app 16-editor avyx-editor "$DEMO/Documents/notes.txt"
app 17-photos avyx-photos
app 18-photo-view avyx-photos "$DEMO/Pictures/sunset.jpg"
app 19-screenshot avyx-screenshot

ctl files 1
