#!/bin/bash
# Brand live-build's GRUB and syslinux screens with AVYX and make them auto-boot.
# Runs inside the build container after `lb config`. Prints the resulting configs so CI
# logs show exactly what was shipped (templates differ a little between live-build releases).
set -euo pipefail
cd "$(dirname "$0")/.."

SRC=/usr/share/live/build/bootloaders
DST=config/bootloaders
[ -d "$SRC" ] || { echo "brand-bootloaders: $SRC not found"; exit 1; }

mkdir -p "$DST"
cp -a "$SRC"/. "$DST"/

echo "== bootloader template files =="
find "$DST" -type f | sort

# 1) live-build ships ONE splash.svg (the Debian helmet plus build/version text) and renders it
#    to splash.png for both GRUB and syslinux. Replace it with an SVG that only embeds the
#    AVYX image, so even if the PNG overrides below are skipped nothing Debian-branded shows.
b64="$(base64 -w0 branding/isolinux-splash.png)"
cat > "$DST/splash.svg" <<EOF
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="640" height="480" viewBox="0 0 640 480">
  <rect width="640" height="480" fill="#000"/>
  <image width="640" height="480" xlink:href="data:image/png;base64,${b64}"/>
</svg>
EOF

# 2) Exact-size PNG overrides applied at the very end of the build (config/includes.binary):
#    16:9 for GRUB (so nothing is stretched), 4:3 for syslinux.
mkdir -p config/includes.binary/boot/grub config/includes.binary/isolinux
cp -f branding/grub-background.png   config/includes.binary/boot/grub/splash.png
cp -f branding/isolinux-splash.png   config/includes.binary/isolinux/splash.png

# 3) No upstream names or titles on the menus.
while IFS= read -r f; do
  sed -i \
    -e 's#Debian GNU/Linux#AVYX OS#g' \
    -e 's#Debian Live#AVYX OS#g' \
    -e 's#Live system#AVYX OS live#g' \
    -e 's#\bDebian\b#AVYX#g' "$f"
done < <(grep -rIl -e 'Debian' -e 'Live system' "$DST" --include='*.cfg' --include='*.in' --include='*.txt' --include='*.conf' || true)
sed -i 's/^title-text:.*/title-text: ""/' "$DST/grub-pc/live-theme/theme.txt"

# 4) Auto-boot. The upstream templates wait for a keypress forever.
#    GRUB: hidden menu, 3 s (hold Shift or press Esc to open the menu).
#    syslinux: 3 s countdown on the branded menu.
for f in "$DST"/grub-pc/config.cfg; do
  sed -i -e '/^set timeout=/d' -e '/^set timeout_style=/d' "$f"
  printf '\nset timeout=3\nset timeout_style=hidden\n' >> "$f"
done
for f in "$DST"/isolinux/isolinux.cfg "$DST"/syslinux/syslinux.cfg "$DST"/syslinux_common/*.cfg; do
  [ -f "$f" ] || continue
  if grep -qiE '^[[:space:]]*timeout[[:space:]]' "$f"; then
    sed -i -E 's/^([[:space:]]*)timeout[[:space:]].*/\1timeout 30/I' "$f"
  fi
done
grep -qiE '^[[:space:]]*timeout[[:space:]]' "$DST/isolinux/isolinux.cfg" || printf '\ntimeout 30\n' >> "$DST/isolinux/isolinux.cfg"

echo "== result: grub-pc/config.cfg =="; cat "$DST/grub-pc/config.cfg"
echo "== result: grub-pc/grub.cfg ==";   cat "$DST/grub-pc/grub.cfg"
echo "== result: grub-pc/live-theme/theme.txt (head) =="; head -8 "$DST/grub-pc/live-theme/theme.txt"
echo "== result: isolinux/isolinux.cfg =="; cat "$DST/isolinux/isolinux.cfg"
echo "== result: syslinux_common/menu.cfg =="; cat "$DST/syslinux_common/menu.cfg"
echo "== result: syslinux_common/live.cfg.in =="; cat "$DST/syslinux_common/live.cfg.in"
