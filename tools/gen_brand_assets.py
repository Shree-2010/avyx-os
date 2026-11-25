#!/usr/bin/env python3
"""Derive boot/login branding images from the supplied AVYX boot-logo artwork.

Input : branding/avyx-boot-logo-original.png  (1672x941, logo + flare on pure black)
Output: meta-avyx/recipes-avyx/avyx-plymouth-theme/files/{logo.png,bar-track.png,bar-fill.png,bar-glow.png}
        meta-avyx/recipes-avyx/avyx-branding/files/avyx-logo.png (same crop, for the lock/login screens)
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

root = Path(__file__).resolve().parent.parent
src = Image.open(root / "branding/avyx-boot-logo-original.png").convert("RGB")
a = np.asarray(src).astype(np.int32)
a[a < 4] = 0                       # clean up near-black noise so the crop blends with a pure-black screen
crop = Image.fromarray(a.astype(np.uint8)).crop((130, 320, 1542, 640))   # 1412x320, logo + flare + slogan

pl = root / "meta-avyx/recipes-avyx/avyx-plymouth-theme/files"
br = root / "meta-avyx/recipes-avyx/avyx-branding/files"
pl.mkdir(parents=True, exist_ok=True)
br.mkdir(parents=True, exist_ok=True)
crop.save(pl / "logo.png", optimize=True)
crop.save(br / "avyx-logo.png", optimize=True)

# progress bar parts: 1-px-wide images that the Plymouth script scales
def solid(path, rgba, size=(4, 4)):
    Image.new("RGBA", size, rgba).save(path)

solid(pl / "bar-track.png", (255, 255, 255, 38))
# fill: orange -> warm white gradient 256x4
g = np.zeros((4, 256, 4), np.uint8)
for x in range(256):
    t = x / 255
    g[:, x] = (255, int(150 + 80 * t), int(40 + 150 * t), 255)
Image.fromarray(g, "RGBA").save(pl / "bar-fill.png")
# shimmer glow: soft horizontal highlight 96x4
s = np.zeros((4, 96, 4), np.uint8)
for x in range(96):
    v = max(0.0, 1 - abs(x - 48) / 48.0) ** 1.6
    s[:, x] = (255, 235, 200, int(220 * v))
Image.fromarray(s, "RGBA").save(pl / "bar-glow.png")
print("ok", crop.size)
