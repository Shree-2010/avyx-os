#!/bin/bash
# Builds the AVYX OS live ISO. Runs as root inside a debian:trixie container, repo mounted at /work.
set -euxo pipefail
cd "$(dirname "$0")/.."

VER="${AVYX_VERSION:-0.1.0-dev}"
export DEBIAN_FRONTEND=noninteractive
mkdir -p out build-logs

# All Debian components, so firmware and codecs resolve.
for f in /etc/apt/sources.list.d/debian.sources; do
  [ -f "$f" ] && sed -i 's/^Components: main$/Components: main contrib non-free non-free-firmware/' "$f"
done
apt-get update
apt-get install -y --no-install-recommends \
  live-build debootstrap squashfs-tools xorriso mtools dosfstools ca-certificates \
  grub-pc-bin grub-efi-amd64-bin syslinux syslinux-common syslinux-utils isolinux \
  gnupg curl

# Version string visible inside the image.
mkdir -p config/includes.chroot_after_packages/etc
printf '%s\n' "$VER" > config/includes.chroot_after_packages/etc/avyx-version

lb clean --purge || true

lb config \
  --mode debian \
  --distribution trixie \
  --architectures amd64 \
  --binary-images iso-hybrid \
  --bootloaders "grub-efi,syslinux" \
  --linux-flavours amd64 \
  --archive-areas "main contrib non-free non-free-firmware" \
  --apt-recommends false \
  --apt-indices false \
  --debian-installer none \
  --memtest none \
  --win32-loader false \
  --security true --updates true --backports false \
  --image-name avyx-os \
  --iso-application "AVYX OS" \
  --iso-publisher "AVYX; https://github.com/Shree-2010/avyx-os" \
  --iso-volume "AVYX_OS" \
  --chroot-squashfs-compression-type zstd \
  --chroot-squashfs-compression-level 19 \
  --bootappend-live "boot=live components quiet splash username=avyx hostname=avyx locales=en_US.UTF-8 timezone=Asia/Kolkata keyboard-layouts=us plymouth.ignore-serial-consoles console=ttyS0,115200 console=tty0"

bash tools/brand-bootloaders.sh 2>&1 | tee build-logs/bootloaders.log
bash tools/filter-packages.sh build-logs/dropped-packages.txt config/package-lists/*.list.chroot

echo "== effective package list =="
cat config/package-lists/*.list.chroot | grep -v '^#' | tr ' ' '\n' | sort -u | tee build-logs/package-list.txt | wc -l

set +e
lb build 2>&1 | tee build-logs/lb-build.log
rc=${PIPESTATUS[0]}
set -e

if [ "$rc" -ne 0 ]; then
  echo "lb build failed with exit code $rc"
  tail -n 80 build-logs/lb-build.log || true
  exit "$rc"
fi

# Evidence for installer tuning: what Calamares actually ships with in this image.
mkdir -p build-logs/calamares
cp -r chroot/etc/calamares build-logs/calamares/etc 2>/dev/null || true
cp -r chroot/usr/share/calamares build-logs/calamares/share 2>/dev/null || true
grep -A12 '^Package: calamares' chroot/var/lib/dpkg/status > build-logs/calamares/dpkg-status.txt 2>/dev/null || true
ls chroot/usr/lib/x86_64-linux-gnu/calamares/modules 2>/dev/null > build-logs/calamares/modules-list.txt || true
du -sh chroot/usr/lib/x86_64-linux-gnu/qt5 chroot/usr/lib/x86_64-linux-gnu/qt6 2>/dev/null > build-logs/calamares/qt-sizes.txt || true

iso="$(ls -1 ./*.iso | head -n1)"
final="out/AVYX-OS-${VER}-amd64.iso"
mv "$iso" "$final"
( cd out && sha256sum "$(basename "$final")" > "$(basename "$final").sha256" )
ls -l out
cp -f build-logs/dropped-packages.txt out/ || true
ls ./*.packages >/dev/null 2>&1 && cp -f ./*.packages out/packages.txt || true
gzip -9 -k build-logs/lb-build.log && mv build-logs/lb-build.log.gz out/ || true

if [ -n "${HOST_UID:-}" ]; then chown -R "${HOST_UID}:${HOST_GID:-$HOST_UID}" out build-logs || true; fi
echo "BUILD OK: $final"
