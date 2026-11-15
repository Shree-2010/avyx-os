#!/usr/bin/env python3
"""Generate all original AVYX branding assets.

Everything produced here is original work released under CC0 / MIT.
Run from anywhere:  python3 tools/gen_assets.py
Requires: rsvg-convert, ImageMagick (convert), ffmpeg (libvorbis), Pillow, numpy,
and the Inter font (SIL OFL 1.1) for the slogan image.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
INC = ROOT / "config" / "includes.chroot_after_packages"
BRAND = ROOT / "branding"
INTER_MED = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"

GRAD = ("#7df3ff", "#7a8bff", "#c27bff")  # cyan -> indigo -> violet

# --------------------------------------------------------------------------
# Logo (pure vector, no font dependency: wordmark is built from strokes)
# --------------------------------------------------------------------------
LETTERS = {
    "A": [[(0, 140), (50, 0), (100, 140)], [(24, 98), (76, 98)]],
    "V": [[(0, 0), (50, 140), (100, 0)]],
    "Y": [[(0, 0), (50, 72), (100, 0)], [(50, 72), (50, 140)]],
    "X": [[(0, 0), (100, 140)], [(100, 0), (0, 140)]],
}


def _poly(points, dx=0, dy=0):
    pts = [f"{x + dx:.1f},{y + dy:.1f}" for x, y in points]
    return "M" + " L".join(pts)


def wordmark_paths(stroke_w=15, spacing=38):
    """Return (svg_path_elements, width, height) for the AVYX wordmark."""
    out, x = [], 0
    for ch in "AVYX":
        for stroke in LETTERS[ch]:
            out.append(f'<path d="{_poly(stroke, x, 0)}"/>')
        x += 100 + spacing
    width = x - spacing
    return "\n      ".join(out), width, 140


def mark_svg_group():
    # Two interlocking chevrons: an "A" apex over a "V" point. Translucent strokes so
    # the overlap reads as glass instead of needing a background-coloured outline.
    return """
    <g fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="34">
      <path d="M78 262 L200 72 L322 262" stroke="url(#g)" stroke-opacity=".92"/>
      <path d="M78 138 L200 328 L322 138" stroke="url(#g2)" stroke-opacity=".80"/>
      <path d="M200 72 L322 262" stroke="#ffffff" stroke-opacity=".0" stroke-width="2"/>
    </g>"""


def defs(ww=508):
    return f"""
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{GRAD[0]}"/><stop offset=".55" stop-color="{GRAD[1]}"/>
      <stop offset="1" stop-color="{GRAD[2]}"/>
    </linearGradient>
    <linearGradient id="g2" x1="1" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{GRAD[2]}"/><stop offset=".5" stop-color="{GRAD[1]}"/>
      <stop offset="1" stop-color="{GRAD[0]}"/>
    </linearGradient>
    <linearGradient id="w" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{ww}" y2="0">
      <stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#cfd6fb"/>
    </linearGradient>
  </defs>"""


def build_svgs():
    word, ww, wh = wordmark_paths()
    # standalone mark
    mark = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400">
  <title>AVYX mark</title>{defs()}{mark_svg_group()}
</svg>
"""
    # standalone wordmark
    pad = 20
    wm = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad} {-pad} {ww + 2 * pad} {wh + 2 * pad}">
  <title>AVYX wordmark</title>{defs(ww)}
  <g fill="none" stroke="url(#w)" stroke-width="15" stroke-linecap="round" stroke-linejoin="round">
      {word}
  </g>
</svg>
"""
    # stacked logo: mark above wordmark
    mark_scale = 0.9
    mark_w = 400 * mark_scale
    total_w = max(mark_w, ww) + 2 * pad
    mark_x = (total_w - mark_w) / 2
    word_x = (total_w - ww) / 2
    total_h = 400 * mark_scale + 40 + wh + 2 * pad
    logo = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w:.0f} {total_h:.0f}">
  <title>AVYX</title>{defs(ww)}
  <g transform="translate({mark_x:.1f},{pad}) scale({mark_scale})">{mark_svg_group()}
  </g>
  <g transform="translate({word_x:.1f},{pad + 400 * mark_scale + 40:.1f})" fill="none" stroke="url(#w)"
     stroke-width="15" stroke-linecap="round" stroke-linejoin="round">
      {word}
  </g>
</svg>
"""
    BRAND.mkdir(parents=True, exist_ok=True)
    (BRAND / "avyx-mark.svg").write_text(mark)
    (BRAND / "avyx-wordmark.svg").write_text(wm)
    (BRAND / "avyx-logo.svg").write_text(logo)


def rsvg(svg_path, png_path, width):
    subprocess.run(
        ["rsvg-convert", "-w", str(width), "-b", "none", "-o", str(png_path), str(svg_path)],
        check=True,
    )


def glow_logo(svg_path, out_path, width=900, pad=160):
    """Logo PNG with a soft baked glow, transparent background."""
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "raw.png"
        rsvg(svg_path, raw, width)
        im = Image.open(raw).convert("RGBA")
    canvas = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    canvas.paste(im, (pad, pad))
    alpha = canvas.split()[3]
    halo = Image.new("RGBA", canvas.size, (120, 150, 255, 0))
    halo.putalpha(alpha.filter(ImageFilter.GaussianBlur(34)).point(lambda v: int(v * 0.55)))
    halo2 = Image.new("RGBA", canvas.size, (125, 243, 255, 0))
    halo2.putalpha(alpha.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.35)))
    out = Image.alpha_composite(halo, halo2)
    out = Image.alpha_composite(out, canvas)
    out.save(out_path)
    return out


def slogan_png(out_path, height_px=56):
    subprocess.run(
        [
            "convert", "-background", "none", "-fill", "#a9b3cc",
            "-font", INTER_MED, "-pointsize", str(height_px), "-kerning", "16",
            "label:BUILD BEYOND LIMITS", str(out_path),
        ],
        check=True,
    )


# --------------------------------------------------------------------------
# Plymouth theme
# --------------------------------------------------------------------------
PLYMOUTH_SCRIPT = r"""# AVYX boot splash: black, centred glowing logo, slogan, thin animated bar.
Window.SetBackgroundTopColor(0.0, 0.0, 0.0);
Window.SetBackgroundBottomColor(0.0, 0.0, 0.0);

sw = Window.GetWidth();
sh = Window.GetHeight();

# ---- logo (wordmark only, centred) ----
logo_src = Image("logo.png");
logo_target_w = sw * 0.40;
if (logo_target_w < 420) logo_target_w = 420;
k = logo_target_w / logo_src.GetWidth();
logo_w = Math.Int(logo_src.GetWidth() * k);
logo_h = Math.Int(logo_src.GetHeight() * k);
logo_img = logo_src.Scale(logo_w, logo_h);
logo = Sprite(logo_img);
logo_x = Math.Int((sw - logo_w) / 2);
logo_cy = Math.Int(sh * 0.47);
logo_y = logo_cy - Math.Int(logo_h / 2);
logo.SetPosition(logo_x, logo_y, 10);

# ---- slogan, directly under the wordmark ----
slogan_src = Image("slogan.png");
slogan_target_w = sw * 0.24;
if (slogan_target_w < 240) slogan_target_w = 240;
ks = slogan_target_w / slogan_src.GetWidth();
slogan_w = Math.Int(slogan_src.GetWidth() * ks);
slogan_h = Math.Int(slogan_src.GetHeight() * ks);
slogan_img = slogan_src.Scale(slogan_w, slogan_h);
slogan = Sprite(slogan_img);
slogan.SetPosition(Math.Int((sw - slogan_w) / 2), logo_cy + Math.Int(logo_h * 0.22) + Math.Int(sh * 0.035), 10);

# ---- progress bar ----
bar_w = Math.Int(sw * 0.34);
if (bar_w < 260) bar_w = 260;
bar_h = Math.Int(sh * 0.004);
if (bar_h < 3) bar_h = 3;
bar_x = Math.Int((sw - bar_w) / 2);
bar_y = Math.Int(sh * 0.91);

track_src = Image("bar_track.png");
fill_src = Image("bar_fill.png");
glow_src = Image("bar_glow.png");

track = Sprite(track_src.Scale(bar_w, bar_h));
track.SetPosition(bar_x, bar_y, 20);

fill = Sprite();
fill.SetPosition(bar_x, bar_y, 21);

glow_w = Math.Int(bar_w * 0.22);
glow = Sprite(glow_src.Scale(glow_w, bar_h * 3));
glow.SetPosition(bar_x, bar_y - bar_h, 22);
glow.SetOpacity(0.0);

counter = 0;
target = 0.0;
shown = 0.0;

fun refresh_cb() {
    counter++;
    # ease towards the real boot progress, and creep a little so it never looks frozen
    shown = shown + (target - shown) * 0.06;
    if (shown < 0.92) shown = shown + 0.0006;
    if (shown > 1.0) shown = 1.0;

    fw = Math.Int(bar_w * shown);
    if (fw < 2) fw = 2;
    fill.SetImage(fill_src.Scale(fw, bar_h));

    # travelling highlight inside the filled part of the bar
    if (fw > glow_w) {
        phase = (counter % 90) / 90.0;
        gx = bar_x + Math.Int((fw - glow_w) * phase);
        glow.SetPosition(gx, bar_y - bar_h, 22);
        glow.SetOpacity(0.85);
    } else {
        glow.SetOpacity(0.0);
    }

    # subtle breathing glow on the logo
    logo.SetOpacity(0.93 + 0.07 * Math.Sin(counter / 22.0));
}
Plymouth.SetRefreshFunction(refresh_cb);

fun progress_cb(duration, progress) {
    target = progress;
}
Plymouth.SetBootProgressFunction(progress_cb);

fun quit_cb() {
    target = 1.0;
    shown = 1.0;
}
Plymouth.SetQuitFunction(quit_cb);

# No text prompts in the splash; keep these defined so nothing breaks.
fun message_cb(text) { }
Plymouth.SetMessageFunction(message_cb);
"""

PLYMOUTH_FILE = """[Plymouth Theme]
Name=AVYX
Description=AVYX boot splash
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/avyx
ScriptFile=/usr/share/plymouth/themes/avyx/avyx.script
"""


def build_plymouth(glow_img):
    d = INC / "usr/share/plymouth/themes/avyx"
    d.mkdir(parents=True, exist_ok=True)
    glow_img.save(d / "logo.png")
    slogan_png(d / "slogan.png")
    Image.new("RGBA", (8, 4), (255, 255, 255, 40)).save(d / "bar_track.png")
    Image.new("RGBA", (8, 4), (205, 225, 255, 235)).save(d / "bar_fill.png")
    # horizontal highlight gradient for the shimmer
    g = np.zeros((4, 128, 4), dtype=np.uint8)
    xs = np.linspace(0, 1, 128)
    a = (np.sin(xs * np.pi) ** 2 * 255).astype(np.uint8)
    g[..., 0], g[..., 1], g[..., 2], g[..., 3] = 140, 245, 255, a[None, :]
    Image.fromarray(g, "RGBA").save(d / "bar_glow.png")
    (d / "avyx.script").write_text(PLYMOUTH_SCRIPT)
    (d / "avyx.plymouth").write_text(PLYMOUTH_FILE)


# --------------------------------------------------------------------------
# Wallpapers
# --------------------------------------------------------------------------
def _wallpaper(w, h, dark, seed):
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    aspect = w / h
    if dark:
        top, bot = np.array([4, 6, 15], np.float32), np.array([11, 15, 42], np.float32)
        blobs = [
            (0.18, 0.78, 0.55, (40, 205, 255), 0.55),
            (0.78, 0.22, 0.50, (125, 95, 255), 0.65),
            (0.55, 1.00, 0.42, (255, 95, 205), 0.33),
            (0.95, 0.80, 0.34, (70, 255, 205), 0.22),
        ]
        band_amp = 0.10
    else:
        top, bot = np.array([238, 242, 252], np.float32), np.array([218, 227, 250], np.float32)
        blobs = [
            (0.18, 0.78, 0.55, (140, 220, 255), 0.55),
            (0.78, 0.22, 0.50, (190, 170, 255), 0.55),
            (0.55, 1.00, 0.42, (255, 180, 225), 0.40),
            (0.95, 0.80, 0.34, (170, 255, 225), 0.30),
        ]
        band_amp = 0.35
    img = (top[None, None, :] * (1 - y[..., None]) + bot[None, None, :] * y[..., None]) * np.ones(
        (1, w, 1), np.float32
    )
    for cx, cy, r, col, amp in blobs:
        d2 = ((x - cx) * aspect) ** 2 + (y - cy) ** 2
        g = np.exp(-d2 / (2 * (r / 2.3) ** 2)) * amp
        col = np.array(col, np.float32)
        if dark:
            img += g[..., None] * col[None, None, :]
        else:
            img = img * (1 - g[..., None]) + col[None, None, :] * g[..., None]
    # soft diagonal light bands (glass reflections)
    for c, s, amp in ((0.35, 0.06, band_amp), (0.62, 0.025, band_amp * 0.6)):
        t = (x * aspect * 0.7 + y * 0.7) / (aspect * 0.7 + 0.7)
        b = np.exp(-((t - c) ** 2) / (2 * s * s)) * amp
        img += b[..., None] * (255.0 if dark else 255.0) * (0.35 if dark else 0.25)
    # vignette
    v = 1 - 0.28 * (((x - 0.5) * 1.3) ** 2 + ((y - 0.5) * 1.3) ** 2)
    img *= np.clip(v, 0.55, 1.0)[..., None]
    # fine grain so gradients never band
    img += rng.normal(0, 1.1, size=(h, w, 1)).astype(np.float32)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def build_wallpapers():
    specs = [("AVYX-Aurora", "AVYX Aurora", True, 11), ("AVYX-Dawn", "AVYX Dawn", False, 23)]
    for ident, name, dark, seed in specs:
        base = _wallpaper(3840, 2160, dark, seed)
        d = INC / f"usr/share/wallpapers/{ident}"
        (d / "contents/images").mkdir(parents=True, exist_ok=True)
        for (w, h) in ((3840, 2160), (2560, 1440), (1920, 1080), (1366, 768), (1920, 1200)):
            im = base if (w, h) == (3840, 2160) else base.resize((w, h), Image.LANCZOS)
            im.save(d / f"contents/images/{w}x{h}.jpg", quality=88, optimize=True)
        base.resize((600, 338), Image.LANCZOS).save(d / "contents/screenshot.jpg", quality=85)
        meta = {
            "KPlugin": {
                "Authors": [{"Name": "AVYX"}],
                "Id": ident,
                "License": "CC0-1.0",
                "Name": name,
            }
        }
        (d / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
        if dark:
            base.resize((1920, 1080), Image.LANCZOS).save(BRAND / "wallpaper-aurora.jpg", quality=85)


# --------------------------------------------------------------------------
# Bootloader backgrounds (GRUB 1920x1080, syslinux 640x480)
# --------------------------------------------------------------------------
def build_boot_backgrounds(glow_img):
    # Same layout as the Plymouth splash (avyx.script): logo block centred at 46% of the
    # screen height, slogan tucked under it, thin progress bar at 91%.
    def compose(w, h, logo_h_frac=0.34, bar=False, bar_fill=0.55):
        bg = Image.new("RGB", (w, h), (0, 0, 0))
        lh = int(h * logo_h_frac)
        lw = int(glow_img.width * lh / glow_img.height)
        lg = glow_img.resize((lw, lh), Image.LANCZOS)
        top = int(h * 0.46 - lh / 2)
        bg.paste(lg, ((w - lw) // 2, top), lg)
        with tempfile.TemporaryDirectory() as td:
            sl = Path(td) / "s.png"
            slogan_png(sl, 44)
            s = Image.open(sl).convert("RGBA")
            sw_ = max(int(w * 0.26), 220 if w >= 1000 else 150)
            s = s.resize((sw_, int(s.height * sw_ / s.width)), Image.LANCZOS)
            bg.paste(s, ((w - sw_) // 2, top + lh - int(h * 0.035)), s)
        if bar:
            bw, bh = max(int(w * 0.34), 260), max(int(h * 0.004), 3)
            bx, by = (w - bw) // 2, int(h * 0.91)
            bg.paste((40, 42, 52), (bx, by, bx + bw, by + bh))
            bg.paste((205, 225, 255), (bx, by, bx + int(bw * bar_fill), by + bh))
        return bg

    compose(1920, 1080).save(BRAND / "grub-background.png")
    compose(640, 480, 0.30).save(BRAND / "isolinux-splash.png")
    compose(1920, 1080, bar=True).save(BRAND / "splash-preview.png")


# --------------------------------------------------------------------------
# Sound theme (original synthesis, no samples from anywhere)
# --------------------------------------------------------------------------
SR = 48000


def _t(dur):
    return np.arange(int(SR * dur)) / SR


def bell(freq, dur=1.4, amp=0.5, ratio=3.01, index=2.2, decay=3.2):
    t = _t(dur)
    env = np.exp(-decay * t) * np.minimum(1, t / 0.004)
    idx = index * np.exp(-2.5 * t)
    y = np.sin(2 * np.pi * freq * t + idx * np.sin(2 * np.pi * freq * ratio * t))
    y += 0.25 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-5 * t)
    return amp * env * y


def tone(freq, dur=0.3, amp=0.4, decay=7.0):
    t = _t(dur)
    env = np.exp(-decay * t) * np.minimum(1, t / 0.006)
    tri = (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * freq * t))
    return amp * env * (0.7 * tri + 0.3 * np.sin(2 * np.pi * freq * t))


def noise_burst(dur=0.05, amp=0.5, lo=1500, hi=6500, seed=1):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, int(SR * dur))
    spec = np.fft.rfft(n)
    f = np.fft.rfftfreq(len(n), 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(spec, len(n))
    y /= np.max(np.abs(y)) + 1e-9
    t = _t(dur)
    return amp * y * np.exp(-60 * t)


def mix(parts, total):
    out = np.zeros(int(SR * total))
    for start, sig in parts:
        i = int(SR * start)
        out[i : i + len(sig)] += sig[: len(out) - i]
    return out


def reverb(x, wet=0.28, rt=0.9, seed=3):
    rng = np.random.default_rng(seed)
    n = int(SR * rt)
    ir = rng.normal(0, 1, n) * np.exp(-5.5 * np.arange(n) / n)
    ir[0] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)
    x_pad = np.pad(x, (0, L - len(x)))
    return (1 - wet) * x_pad + wet * y


def finish(x, fade=0.04):
    x = x[: int(np.max(np.nonzero(np.abs(x) > 1e-4)) + 1)] if np.any(np.abs(x) > 1e-4) else x
    f = int(SR * fade)
    x[-f:] *= np.linspace(1, 0, f)
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.7
    # slight stereo widening
    l = x
    r = np.concatenate([np.zeros(24), x[:-24]])
    return np.stack([l, r], axis=1)


def seq(notes, dur, amp, **kw):
    return mix([(t0, bell(f, dur, amp, **kw)) for f, t0 in notes], notes[-1][1] + dur)


def build_sounds():
    d = INC / "usr/share/sounds/avyx/stereo"
    d.mkdir(parents=True, exist_ok=True)
    (d.parent / "index.theme").write_text(
        "[Sound Theme]\nName=AVYX\nComment=Original AVYX sound theme (CC0)\n"
        "Directories=stereo\n\n[stereo]\nOutputProfile=stereo\n"
    )
    S = {}
    S["desktop-login"] = reverb(seq([(392.0, 0), (587.3, 0.13), (880.0, 0.26), (1318.5, 0.42)], 2.2, 0.5, decay=1.8), 0.35, 1.6)
    S["desktop-logout"] = reverb(seq([(1318.5, 0), (880.0, 0.12), (587.3, 0.24), (392.0, 0.38)], 1.6, 0.45, decay=2.4), 0.3, 1.2)
    S["message-new-instant"] = reverb(seq([(1046.5, 0), (1568.0, 0.11)], 0.8, 0.5, decay=4.5), 0.22, 0.6)
    S["message"] = S["message-new-instant"]
    S["bell"] = reverb(bell(880.0, 0.5, 0.45, decay=7), 0.18, 0.4)
    S["dialog-information"] = reverb(bell(1174.7, 0.6, 0.45, decay=5.5), 0.2, 0.5)
    S["dialog-question"] = reverb(seq([(659.3, 0), (880.0, 0.1)], 0.5, 0.45, decay=6), 0.2, 0.5)
    S["dialog-warning"] = mix([(0, tone(660, 0.3, 0.5)), (0.17, tone(494, 0.4, 0.5))], 0.6)
    S["dialog-error"] = mix([(0, tone(330, 0.3, 0.55)), (0.15, tone(247, 0.3, 0.55)), (0.3, tone(185, 0.5, 0.55))], 0.85)
    S["device-added"] = reverb(seq([(587.3, 0), (880.0, 0.1)], 0.6, 0.45, decay=6), 0.2, 0.5)
    S["device-removed"] = reverb(seq([(880.0, 0), (587.3, 0.1)], 0.6, 0.45, decay=6), 0.2, 0.5)
    S["audio-volume-change"] = tone(1200, 0.07, 0.5, decay=40)
    S["window-close"] = tone(520, 0.08, 0.4, decay=35)
    S["power-plug"] = reverb(seq([(659.3, 0), (987.8, 0.09)], 0.5, 0.45, decay=7), 0.15, 0.4)
    S["power-unplug"] = reverb(seq([(987.8, 0), (659.3, 0.09)], 0.5, 0.45, decay=7), 0.15, 0.4)
    S["battery-low"] = mix([(i * 0.28, tone(440, 0.2, 0.5, 9)) for i in range(3)], 0.9)
    S["complete"] = reverb(seq([(784.0, 0), (987.8, 0.09), (1174.7, 0.18)], 0.7, 0.45, decay=5), 0.2, 0.5)
    S["camera-shutter"] = mix([(0, noise_burst(0.045, 0.6, seed=1)), (0.07, noise_burst(0.06, 0.5, 900, 4200, seed=2))], 0.2)
    S["screen-capture"] = S["camera-shutter"]
    S["trash-empty"] = noise_burst(0.45, 0.35, 800, 5000, seed=5) * np.linspace(1, 0.1, int(SR * 0.45))
    with tempfile.TemporaryDirectory() as td:
        for name, sig in S.items():
            wav = Path(td) / f"{name}.wav"
            st = finish(sig.copy())
            import wave

            with wave.open(str(wav), "wb") as w:
                w.setnchannels(2)
                w.setsampwidth(2)
                w.setframerate(SR)
                w.writeframes((st * 32767).astype("<i2").tobytes())
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis", "-q:a", "4", str(d / f"{name}.oga")],
                check=True,
            )


# --------------------------------------------------------------------------
# KDE colour schemes (original palettes)
# --------------------------------------------------------------------------
def _scheme(name, p):
    def grp(title, bg, alt, fg, inact, act, link, vis, neg, neu, pos, focus, hover):
        return (
            f"[Colors:{title}]\nBackgroundAlternate={alt}\nBackgroundNormal={bg}\nDecorationFocus={focus}\n"
            f"DecorationHover={hover}\nForegroundActive={act}\nForegroundInactive={inact}\nForegroundLink={link}\n"
            f"ForegroundNegative={neg}\nForegroundNeutral={neu}\nForegroundNormal={fg}\nForegroundPositive={pos}\n"
            f"ForegroundVisited={vis}\n\n"
        )
    c = p
    out = ""
    out += grp("Button", c["btn"], c["btn_alt"], c["fg"], c["fg_dim"], c["cyan"], c["link"], c["violet"], c["neg"], c["neu"], c["pos"], c["accent"], c["cyan"])
    out += grp("Complementary", c["comp"], c["win_alt"], c["fg"], c["fg_dim"], c["cyan"], c["link"], c["violet"], c["neg"], c["neu"], c["pos"], c["accent"], c["cyan"])
    out += grp("Header", c["win"], c["win_alt"], c["fg"], c["fg_dim"], c["cyan"], c["link"], c["violet"], c["neg"], c["neu"], c["pos"], c["accent"], c["cyan"])
    out += grp("Selection", c["accent"], c["accent_alt"], "255,255,255", "232,235,255", "255,255,255", "255,255,255", "255,255,255", c["neg"], c["neu"], c["pos"], c["cyan"], c["cyan"])
    out += grp("Tooltip", c["tip"], c["win_alt"], c["fg"], c["fg_dim"], c["cyan"], c["link"], c["violet"], c["neg"], c["neu"], c["pos"], c["accent"], c["cyan"])
    out += grp("View", c["view"], c["view_alt"], c["fg"], c["fg_dim"], c["cyan"], c["link"], c["violet"], c["neg"], c["neu"], c["pos"], c["accent"], c["cyan"])
    out += grp("Window", c["win"], c["win_alt"], c["fg"], c["fg_dim"], c["cyan"], c["link"], c["violet"], c["neg"], c["neu"], c["pos"], c["accent"], c["cyan"])
    out += (
        "[ColorEffects:Disabled]\nColor=56,56,56\nColorAmount=0\nColorEffect=0\nContrastAmount=0.65\n"
        "ContrastEffect=1\nIntensityAmount=0.1\nIntensityEffect=2\n\n"
        "[ColorEffects:Inactive]\nChangeSelectionColor=true\nColor=112,111,110\nColorAmount=0.025\nColorEffect=2\n"
        "ContrastAmount=0.1\nContrastEffect=2\nEnable=false\nIntensityAmount=0\nIntensityEffect=0\n\n"
        f"[General]\nColorScheme={name.replace(' ', '')}\nName={name}\nshadeSortColumn=true\n\n"
        f"[KDE]\ncontrast=4\n\n[WM]\nactiveBackground={c['win']}\nactiveBlend={c['fg']}\nactiveForeground={c['fg']}\n"
        f"inactiveBackground={c['win']}\ninactiveBlend={c['fg_dim']}\ninactiveForeground={c['fg_dim']}\n"
    )
    return out


def build_colorschemes():
    d = INC / "usr/share/color-schemes"
    d.mkdir(parents=True, exist_ok=True)
    dark = dict(win="20,23,36", win_alt="26,30,46", view="13,15,27", view_alt="19,22,36", btn="34,38,58", btn_alt="42,47,70",
                comp="16,18,32", tip="24,27,44", fg="232,235,250", fg_dim="150,157,184", accent="110,125,255",
                accent_alt="96,110,240", cyan="125,243,255", violet="194,123,255", link="125,160,255",
                neg="255,107,129", neu="255,201,107", pos="94,230,160")
    light = dict(win="240,243,252", win_alt="231,235,248", view="252,253,255", view_alt="243,246,253", btn="226,231,247",
                 btn_alt="216,222,243", comp="228,233,248", tip="250,251,255", fg="24,28,48", fg_dim="98,106,138",
                 accent="86,100,235", accent_alt="72,86,220", cyan="20,150,190", violet="140,70,220", link="60,90,220",
                 neg="205,50,80", neu="190,125,10", pos="25,150,90")
    (d / "AVYXDark.colors").write_text(_scheme("AVYX Dark", dark))
    (d / "AVYXLight.colors").write_text(_scheme("AVYX Light", light))


def build_misc_logos(glow_img):
    cal = INC / "etc/calamares/branding/avyx"
    cal.mkdir(parents=True, exist_ok=True)
    lg = glow_img.copy()
    lg.thumbnail((420, 420), Image.LANCZOS)
    lg.save(cal / "logo.png")
    spl = INC / "usr/share/plasma/look-and-feel/org.avyx.desktop/contents/splash/images"
    spl.mkdir(parents=True, exist_ok=True)
    lg2 = glow_img.copy()
    lg2.thumbnail((640, 640), Image.LANCZOS)
    lg2.save(spl / "logo.png")


def main():
    build_svgs()
    glow = glow_logo(BRAND / "avyx-logo.svg", ROOT / "branding" / "avyx-logo-glow.png")
    boot_glow = glow_logo(BRAND / "avyx-wordmark.svg", ROOT / "branding" / "avyx-wordmark-glow.png")
    build_plymouth(boot_glow)
    build_wallpapers()
    build_boot_backgrounds(boot_glow)
    build_sounds()
    build_colorschemes()
    build_misc_logos(glow)
    print("assets generated")


if __name__ == "__main__":
    main()
