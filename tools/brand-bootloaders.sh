#!/bin/bash
# Copy live-build's bootloader templates into config/bootloaders and apply AVYX branding.
# Runs inside the build container after `lb config`. Prints what it found so CI logs show
# the real template layout (it differs a little between live-build releases).
set -euo pipefail
cd "$(dirname "$0")/.."

SRC=/usr/share/live/build/bootloaders
DST=config/bootloaders
[ -d "$SRC" ] || { echo "brand-bootloaders: $SRC not found, skipping"; exit 0; }

mkdir -p "$DST"
cp -a "$SRC"/. "$DST"/

echo "== bootloader template files =="
find "$DST" -type f | sort

# Replace backgrounds / splash images wherever live-build ships them.
while IFS= read -r f; do
  case "$(basename "$f")" in
    background.png) cp -f branding/grub-background.png "$f"; echo "replaced $f" ;;
    splash.png)     cp -f branding/isolinux-splash.png "$f"; echo "replaced $f" ;;
  esac
done < <(find "$DST" -type f \( -name background.png -o -name splash.png \))

# Rewrite visible distribution names in text templates.
while IFS= read -r f; do
  sed -i \
    -e 's#Debian GNU/Linux#AVYX OS#g' \
    -e 's#Debian Live#AVYX OS#g' \
    -e 's#Live system#AVYX OS live#g' \
    -e 's#\bDebian\b#AVYX#g' "$f"
done < <(grep -rIl -e 'Debian' -e 'Live system' "$DST" || true)

echo "== theme.txt (for reference) =="
find "$DST" -name theme.txt -exec sh -c 'echo "--- $1"; cat "$1"' _ {} \; || true
