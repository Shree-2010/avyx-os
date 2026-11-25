#!/usr/bin/env python3
"""AVYX 'Golden Hour' wallpaper: a procedurally drawn dusk scene with an original red suspension bridge.

Everything is generated from code (no photographs, no third-party artwork).
usage: gen_wallpaper.py OUT.jpg [WIDTH HEIGHT]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W = int(sys.argv[2]) if len(sys.argv) > 2 else 1920
H = int(sys.argv[3]) if len(sys.argv) > 3 else int(W * 9 / 16)
OUT = sys.argv[1] if len(sys.argv) > 1 else "golden-hour.jpg"
rng = np.random.default_rng(2610)

HY = 0.43          # horizon (fraction of H)
SUN = (0.584, 0.335)


def smooth(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def fbm(w, h, sx, sy, octaves, seed):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gx = max(2, int(w / max(1.0, sx / 2 ** o)) + 2)
        gy = max(2, int(h / max(1.0, sy / 2 ** o)) + 2)
        g = r.random((gy, gx)).astype(np.float32)
        im = Image.fromarray(g, mode="F").resize((w, h), Image.BICUBIC)
        out += amp * np.asarray(im)
        tot += amp
        amp *= 0.5
    out /= tot
    return (out - out.min()) / (out.max() - out.min() + 1e-6)


def grad(stops, t):
    ts = [s[0] for s in stops]
    return np.stack([np.interp(t, ts, [s[1][c] for s in stops]) for c in range(3)], -1)


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
fx, fy = xx / W, yy / H
hy = HY * H
sx_, sy_ = SUN[0] * W, SUN[1] * H

# ---------------------------------------------------------------- sky
sky_t = np.clip(fy / HY, 0, 1)
sky = grad([
    (0.00, (8, 7, 30)), (0.22, (26, 16, 62)), (0.45, (74, 32, 86)), (0.62, (150, 52, 84)),
    (0.76, (226, 94, 62)), (0.88, (255, 150, 62)), (0.96, (255, 196, 96)), (1.0, (255, 214, 130)),
], sky_t).astype(np.float32)
d = np.sqrt(((xx - sx_) / (0.55 * W)) ** 2 + ((yy - sy_) / (0.42 * H)) ** 2)
glow = np.exp(-(d * 1.6) ** 2)[..., None]
sky = sky + glow * np.array([200, 110, 30], np.float32) * 0.75
dd = np.sqrt((xx - sx_) ** 2 + (yy - sy_) ** 2) / W
halo = np.exp(-(dd / 0.07)) [..., None] * np.array([255, 190, 90], np.float32) * 0.55
sky = sky + halo
disc = smooth(0.021 - dd, -0.002, 0.003)[..., None]
sky = sky * (1 - disc) + disc * np.array([255, 246, 214], np.float32)

# stars (very faint, only in the dark top)
st = (rng.random((H, W)) > 0.9993).astype(np.float32) * smooth(0.22 - fy, 0, 0.2)
st = np.asarray(Image.fromarray((st * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32) / 255
sky += st[..., None] * 230

# clouds
cl_n = fbm(W, H, 0.55 * W, 0.075 * H, 6, 11)
cl_n2 = fbm(W, H, 0.9 * W, 0.2 * H, 4, 12)
band = smooth(fy, 0.04, 0.16) * (1 - smooth(fy, 0.34, 0.43))
cm = smooth(cl_n * 0.75 + cl_n2 * 0.25 + band * 0.22, 0.60, 0.86) * band
edge = np.gradient(cl_n, axis=0) * H * 0.35         # lit from below-sun
lit = np.clip(-edge * 6 + 0.35, 0, 1)
sunprox = np.exp(-(np.sqrt((fx - SUN[0]) ** 2 + ((fy - SUN[1]) * 1.4) ** 2) / 0.62) ** 2)
cloud_dark = np.array([58, 28, 74], np.float32)
cloud_lit = np.array([255, 128, 52], np.float32)
cc = cloud_dark + (cloud_lit - cloud_dark) * np.clip(lit * 0.55, 0, 1)[..., None] * (0.35 + 0.8 * sunprox[..., None])
cc = cc + np.array([90, 30, 10], np.float32) * (fy[..., None] > 0.2) * sunprox[..., None] * 0.5
sky = sky * (1 - cm[..., None] * 0.92) + cc * cm[..., None] * 0.92

img = sky.copy()

# ---------------------------------------------------------------- water
wm = (yy >= hy).astype(np.float32)
depth = np.clip((yy - hy) / (H - hy), 0, 1)
rip = fbm(W, H, 0.5 * W, 0.012 * H, 4, 21) - 0.5
src_y = np.clip(hy - (yy - hy) * 0.92 + rip * H * 0.03 * (0.3 + depth), 0, H - 1).astype(np.int32)
src_x = np.clip(xx + rip * W * 0.02 * (0.3 + depth), 0, W - 1).astype(np.int32)
refl = sky[src_y, src_x]
deep = np.array([18, 14, 46], np.float32)
wcol = refl * (0.62 - 0.30 * depth[..., None]) + deep * (0.30 + 0.45 * depth[..., None])
# glitter column under the sun
gw = 0.020 * W + 0.16 * (yy - hy)
gl = np.exp(-((xx - sx_) / gw) ** 2) * smooth(yy - hy, -2, 6) * (1 - 0.55 * depth)
streak = fbm(W, H, 0.20 * W, 0.006 * H, 3, 22)
gl = gl * (0.35 + 1.1 * np.clip(streak - 0.25, 0, 1))
wcol = wcol + gl[..., None] * np.array([255, 190, 100], np.float32) * 0.9
img = img * (1 - wm[..., None]) + wcol * wm[..., None]


def poly_mask(draw_fn, ss=2, blur=0.0):
    m = Image.new("L", (W * ss, H * ss), 0)
    dr = ImageDraw.Draw(m)
    draw_fn(dr, ss)
    m = m.resize((W, H), Image.LANCZOS)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(m, np.float32) / 255.0


def composite(color, mask, alpha=1.0):
    global img
    m = (mask * alpha)[..., None]
    img = img * (1 - m) + np.asarray(color, np.float32) * m


# ---------------------------------------------------------------- distant land
def ridge(seed, base, amp, sx, x0=0.0, x1=1.0):
    n = fbm(W, 8, sx, 8, 5, seed)[0]
    xs = np.linspace(0, 1, W)
    line = base - amp * n
    m = np.clip((xs - x0) / 0.02, 0, 1) * np.clip((x1 - xs) / 0.02, 0, 1)
    return line, m


# far hazy headland on the right + city skyline
def city(dr, ss):
    x = 0.60
    r2 = np.random.default_rng(7)
    while x < 0.995:
        bw = r2.uniform(0.004, 0.014)
        bh = r2.uniform(0.012, 0.055) * (1.0 + 1.6 * np.exp(-((x - 0.80) / 0.07) ** 2))
        if r2.random() < 0.08:
            bh *= 1.9
        dr.rectangle([x * W * ss, (HY - bh) * H * ss, (x + bw) * W * ss, (HY + 0.004) * H * ss], fill=255)
        x += bw * r2.uniform(0.75, 1.15)
    # one pointed tower
    cx = 0.835
    dr.polygon([(cx * W * ss, (HY - 0.115) * H * ss), ((cx - 0.012) * W * ss, (HY) * H * ss), ((cx + 0.012) * W * ss, (HY) * H * ss)], fill=255)


m_city = poly_mask(city, blur=0.6)
haze_col = np.array([140, 70, 98], np.float32)
composite(haze_col, m_city, 0.78)
# lit windows
win = (rng.random((H, W)) > 0.9965).astype(np.float32) * m_city * smooth(yy - (HY * H - 0.12 * H), 0, 0.1 * H)
win = np.asarray(Image.fromarray((win * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
img += win[..., None] * np.array([255, 190, 110], np.float32) * 1.4

# headland ridges
ln, mk = ridge(31, HY + 0.004, 0.05, 0.4 * W, 0.0, 1.0)
rl = poly_mask(lambda dr, ss: dr.polygon([(0, H * ss)] + [(i * ss, ln[i] * H * ss) for i in range(0, W, 3)] + [(W * ss, H * ss)], fill=255))
rl = rl * (yy < hy + 3)
composite(np.array([104, 52, 92], np.float32), rl, 0.55)

# left coast: big dark hill with layered ridges
def left_hill(dr, ss, base, amp, reach, seed, sx):
    n = fbm(W, 8, sx, 8, 5, seed)[0]
    pts = [(0, (HY + 0.2) * H * ss)]
    for i in range(0, W, 3):
        t = i / W
        edge = np.clip(1 - t / reach, 0, 1) ** 0.9
        y = base - amp * edge * (0.55 + 0.7 * n[i])
        pts.append((i * ss, y * H * ss))
    pts.append((W * ss, (HY + 0.2) * H * ss))
    dr.polygon(pts, fill=255)


for k, (base, amp, reach, col, al) in enumerate([
        (HY + 0.01, 0.20, 0.55, (120, 58, 96), 0.55), (HY + 0.012, 0.17, 0.46, (74, 38, 80), 0.75),
        (HY + 0.016, 0.14, 0.36, (36, 22, 58), 0.92)]):
    m = poly_mask(lambda dr, ss, b=base, a=amp, r=reach, s=40 + k: left_hill(dr, ss, b, a, r, s, 0.25 * W))
    composite(np.array(col, np.float32), m, al)

# ---------------------------------------------------------------- the bridge (original design)
SS = 3
bl = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
bd = ImageDraw.Draw(bl)


def P(x, y):
    return (x * W * SS, y * H * SS)


def tower(cx, top, base, width, leg, col_lit, col_dark, braces):
    """Two legs, tapering, with portal struts and a top cap. cx centre, widths in fractions of W."""
    hw = width / 2
    for sgn in (-1, 1):
        x_top = cx + sgn * (hw * 0.82)
        x_bot = cx + sgn * hw
        poly = [P(x_top - leg * 0.5, top), P(x_top + leg * 0.5, top), P(x_bot + leg * 0.62, base), P(x_bot - leg * 0.62, base)]
        bd.polygon(poly, fill=col_dark)
        bd.polygon([P(x_top, top), P(x_top + leg * 0.5, top), P(x_bot + leg * 0.62, base), P(x_bot, base)], fill=col_lit)
    for f in braces:
        y = top + (base - top) * f
        hh = (base - top) * 0.018
        xl = cx - hw * (0.82 + 0.18 * f)
        xr = cx + hw * (0.82 + 0.18 * f)
        bd.rectangle([P(xl, y), P(xr, y + hh)], fill=col_dark)
        bd.rectangle([P(xl, y), P(xr, y + hh * 0.35)], fill=col_lit)
    bd.rectangle([P(cx - hw * 0.9, top - (base - top) * 0.02), P(cx + hw * 0.9, top + (base - top) * 0.012)], fill=col_dark)


lit1, dark1 = (255, 118, 52, 255), (150, 38, 34, 255)
lit2, dark2 = (236, 104, 56, 255), (128, 40, 52, 255)

# geometry: near tower (big, left of centre) and far tower
T1 = dict(cx=0.262, top=0.150, base=0.46, width=0.082, leg=0.020)
T2 = dict(cx=0.532, top=0.262, base=0.436, width=0.040, leg=0.0095)
deck1, deck2 = 0.425, 0.437          # deck heights at the towers
# deck (the road): from lower-left foreground up past tower 1 and on to the far tower and shore
deck_pts = [(-0.03, 0.495), (0.10, 0.455), (T1["cx"], deck1), (T2["cx"], deck2), (0.745, 0.441)]
for (xa, ya), (xb, yb) in zip(deck_pts, deck_pts[1:]):
    th = 0.0075 * (1.0 - 0.8 * (xa / 0.75))
    bd.polygon([P(xa, ya), P(xb, yb), P(xb, yb + th), P(xa, ya + th * 1.2)], fill=(92, 26, 34, 255))
    bd.line([P(xa, ya), P(xb, yb)], fill=(255, 146, 72, 255), width=max(1, int(1.6 * SS * W / 1536)))


def cable(x0, y0, x1, y1, sag, n=90, width=2.0):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        pts.append(P(x, y))
    bd.line(pts, fill=(255, 128, 60, 255), width=int(width * SS * W / 1536), joint="curve")
    return pts


def suspenders(x0, y0, x1, y1, sag, deck_fn, step, width=1.0):
    n = int(abs(x1 - x0) / step)
    for i in range(1, n):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        bd.line([P(x, y), P(x, deck_fn(x))], fill=(255, 120, 60, 200), width=max(1, int(width * SS * W / 1536)))


def deck_y(x):
    for (xa, ya), (xb, yb) in zip(deck_pts, deck_pts[1:]):
        if xa <= x <= xb:
            return ya + (yb - ya) * (x - xa) / (xb - xa)
    return deck_pts[-1][1]


t1 = (T1["cx"], T1["top"] + 0.012)
t2 = (T2["cx"], T2["top"] + 0.008)
# main span cables (two, slightly offset for depth)
for off, wd in ((0.0, 2.6), (0.006, 1.5)):
    cable(t1[0], t1[1] + off, t2[0], t2[1] + off, 0.105 - off, width=wd)
suspenders(t1[0], t1[1], t2[0], t2[1], 0.105, deck_y, 0.0048)
# side spans (to the left shore and to the right shore)
cable(t1[0], t1[1], -0.03, 0.43, 0.04, width=2.4)
suspenders(t1[0], t1[1], -0.03, 0.43, 0.04, deck_y, 0.0062)
cable(t2[0], t2[1], 0.745, 0.405, 0.012, width=1.5)
suspenders(t2[0], t2[1], 0.745, 0.405, 0.012, deck_y, 0.0034, width=0.8)

tower(**T2, col_lit=lit2, col_dark=dark2, braces=[0.18, 0.40, 0.62, 0.84])
tower(**T1, col_lit=lit1, col_dark=dark1, braces=[0.16, 0.34, 0.52, 0.70, 0.86])

bl = bl.resize((W, H), Image.LANCZOS)
bl_a = np.asarray(bl, np.float32) / 255.0
bridge_rgb = bl_a[..., :3] * 255.0
bridge_a = bl_a[..., 3]
# atmospheric perspective: the far parts get hazier
far = smooth(fx, 0.25, 0.80)[..., None]
bridge_rgb = bridge_rgb * (1 - 0.45 * far) + np.array([120, 60, 90], np.float32) * 0.45 * far
img = img * (1 - bridge_a[..., None]) + bridge_rgb * bridge_a[..., None]
# warm rim glow around the bridge
gl_b = np.asarray(Image.fromarray((bridge_a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5 * W / 1536)), np.float32) / 255.0
img += gl_b[..., None] * np.array([255, 120, 40], np.float32) * 0.22

# bridge reflection (broken, dim) on the water
refl_m = np.zeros((H, W), np.float32)
ry = np.clip(hy - (yy - hy) * 1.0, 0, H - 1).astype(np.int32)
rx = np.clip(xx + rip * W * 0.03, 0, W - 1).astype(np.int32)
refl_m = bridge_a[ry, rx] * wm * (1 - depth) ** 1.5 * (0.25 + 0.5 * np.clip(streak * 1.8 - 0.4, 0, 1))
img = img * (1 - refl_m[..., None] * 0.6) + np.array([200, 80, 40], np.float32) * refl_m[..., None] * 0.6

# ---------------------------------------------------------------- foreground terrain
def terrain(dr, ss):
    n = fbm(W, 8, 0.30 * W, 8, 5, 52)[0]
    pts = [(0, H * ss)]
    for i in range(0, W, 3):
        t = i / W
        y = 0.84 - 0.30 * np.exp(-(t / 0.20) ** 1.2) - 0.05 * n[i] + 0.04 * t
        pts.append((i * ss, y * H * ss))
    pts.append((W * ss, H * ss))
    dr.polygon(pts, fill=255)


mt = poly_mask(terrain, blur=0.6)
ter_col = np.array([14, 10, 28], np.float32)
composite(ter_col, mt, 0.97)
# subtle top light on the terrain
rim = np.asarray(Image.fromarray((mt * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3 * W / 1536)), np.float32) / 255.0
rim = np.clip(rim - mt, 0, 1)
img += rim[..., None] * np.array([255, 110, 40], np.float32) * 0.6

# winding road with long-exposure light trails
tr = Image.new("RGB", (W * 2, H * 2), (0, 0, 0))
td = ImageDraw.Draw(tr)


def bez(p0, p1, p2, p3, n=120):
    pts = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3
        b = 3 * (1 - t) ** 2 * t
        c = 3 * (1 - t) * t * t
        e = t ** 3
        pts.append(((a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0]) * W * 2, (a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1]) * H * 2))
    return pts


road = bez((0.00, 0.69), (0.14, 0.76), (0.30, 0.86), (0.48, 0.96))
for off, col, wd in ((0.000, (255, 140, 60), 5), (0.006, (255, 198, 120), 3), (-0.006, (255, 90, 40), 3), (0.012, (255, 170, 80), 2)):
    pts = [(x + off * W * 2, y) for x, y in road]
    td.line(pts, fill=col, width=int(wd * W / 1536) * 2)
road2 = bez((0.30, 0.70), (0.40, 0.76), (0.52, 0.84), (0.66, 0.99))
for off, col, wd in ((0.0, (255, 120, 50), 3), (0.007, (255, 190, 110), 2)):
    pts = [(x + off * W * 2, y) for x, y in road2]
    td.line(pts, fill=col, width=int(wd * W / 1536) * 2)
tr = tr.resize((W, H), Image.LANCZOS)
tr_a = np.asarray(tr, np.float32)
tr_blur = np.asarray(tr.filter(ImageFilter.GaussianBlur(7 * W / 1536)), np.float32)
trails = (tr_a * 0.9 + tr_blur * 1.4) * mt[..., None]
img += trails

# scattered city lights on the right terrain
lights = (rng.random((H, W)) > 0.9988).astype(np.float32) * mt * smooth(fx, 0.5, 0.9) * smooth(fy, 0.72, 0.9)
lights = np.asarray(Image.fromarray((lights * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0 * W / 1536)), np.float32) / 255
img += lights[..., None] * np.array([255, 170, 80], np.float32) * 2.2

# ---------------------------------------------------------------- fog
fog_n = fbm(W, H, 0.45 * W, 0.05 * H, 6, 61)
fog_band = np.exp(-((fy - 0.50) / 0.075) ** 2) * (0.35 + 0.65 * smooth(1 - fx, 0.0, 0.7))
fog_band2 = np.exp(-((fy - 0.60) / 0.09) ** 2) * smooth(1 - fx, 0.2, 1.0) * 0.7
fog = np.clip((fog_band + fog_band2) * smooth(fog_n, 0.30, 0.78), 0, 1) * 0.55
fog_col = np.array([255, 190, 170], np.float32) * (0.55 + 0.45 * sunprox[..., None]) + np.array([60, 40, 90], np.float32) * (1 - sunprox[..., None])
img = img * (1 - fog[..., None]) + fog_col * fog[..., None]
# the fog must not cover the very dark foreground completely
img = img * (1 - mt[..., None] * 0.0)

# ---------------------------------------------------------------- finishing
vig = 1 - 0.34 * smooth(np.sqrt(((fx - 0.5) / 0.75) ** 2 + ((fy - 0.5) / 0.8) ** 2), 0.55, 1.1)
img *= vig[..., None]
# gentle tone curve + saturation lift
img = np.clip(img, 0, 255) / 255.0
img = img ** 0.97
lum = img.mean(-1, keepdims=True)
img = np.clip(lum + (img - lum) * 1.12, 0, 1)
out = Image.fromarray((img * 255 + 0.5).astype(np.uint8))
# grain after all resizing (avoids JPEG banding in smooth skies)
g = rng.normal(0, 1.25, (H, W, 1))
arr = np.clip(np.asarray(out, np.float32) + g, 0, 255).astype(np.uint8)
Image.fromarray(arr).save(OUT, quality=93, subsampling=0, optimize=True)
print("wrote", OUT, W, H)
