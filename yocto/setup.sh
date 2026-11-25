#!/usr/bin/env bash
# Fetch the pinned Yocto layers and create ./yocto/build with the AVYX configuration.
#   yocto/setup.sh            -> sources in yocto/sources, build dir yocto/build
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/sources"
mkdir -p "$SRC"
while read -r name url rev; do
    [[ -z "${name:-}" || "$name" == \#* ]] && continue
    if [[ ! -d "$SRC/$name/.git" ]]; then
        git init -q "$SRC/$name"
        git -C "$SRC/$name" remote add origin "$url"
    fi
    if ! git -C "$SRC/$name" cat-file -e "$rev^{commit}" 2>/dev/null; then
        git -C "$SRC/$name" fetch -q --depth 1 origin "$rev"
    fi
    git -C "$SRC/$name" checkout -q --force "$rev"
    echo "layer $name @ $(git -C "$SRC/$name" rev-parse --short HEAD)"
done < "$HERE/layers.txt"

BUILD="$HERE/build"
mkdir -p "$BUILD/conf"
REPO="$(cd "$HERE/.." && pwd)"
sed -e "s|@SRC@|$SRC|g" -e "s|@REPO@|$REPO|g" "$HERE/conf/bblayers.conf.in" > "$BUILD/conf/bblayers.conf"
sed -e "s|@SRC@|$SRC|g" -e "s|@REPO@|$REPO|g" "$HERE/conf/local.conf.in"    > "$BUILD/conf/local.conf"
echo "build dir ready: $BUILD"
echo "next:  source $SRC/poky/oe-init-build-env $BUILD && bitbake avyx-image"
