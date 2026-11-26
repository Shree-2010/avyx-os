#!/usr/bin/env python3
"""Generate the AVYX application icon set (original artwork, drawn entirely from code).

usage: gen_icons.py OUTDIR      -> OUTDIR/<name>.png (256x256, RGBA)
Rendered at 1024x1024 and downsampled for clean anti-aliasing.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

N = 1024
C = N // 2


def new():
    return Image.new("RGBA", (N, N), (0, 0, 0, 0))


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def vgrad(top, bot, size=(N, N)):
    w, h = size
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, float)[None, None, :]
    b = np.array(bot, float)[None, None, :]
    arr = (a + (b - a) * t) * np.ones((1, w, 1))
    mode = "RGBA" if len(top) == 4 else "RGB"
    return Image.fromarray(arr.astype(np.uint8), mode).convert("RGBA")


def lgrad(top, bot):
    """vertical 8-bit gradient mask (255 = opaque)."""
    col = np.linspace(top, bot, N)[:, None] * np.ones((1, N))
    return Image.fromarray(col.astype(np.uint8), "L")


def hgrad(left, right, size=(N, N)):
    return vgrad(left, right, (size[1], size[0])).rotate(90, expand=True).transpose(Image.FLIP_TOP_BOTTOM).resize(size)


def dgrad(c1, c2, size=(N, N)):
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = ((xx / w) * 0.5 + (yy / h) * 0.5)[..., None]
    a = np.array(c1, float)[None, None, :]
    b = np.array(c2, float)[None, None, :]
    return Image.fromarray((a + (b - a) * t).astype(np.uint8), "RGB").convert("RGBA")


def squircle(margin=64, n=5.0):
    r = (N - 2 * margin) / 2
    pts = []
    for i in range(1440):
        t = 2 * math.pi * i / 1440
        ct, st = math.cos(t), math.sin(t)
        pts.append((C + r * math.copysign(abs(ct) ** (2 / n), ct), C + r * math.copysign(abs(st) ** (2 / n), st)))
    m = Image.new("L", (N, N), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def shadow(mask, dy=26, blur=26, alpha=0.5):
    s = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    a = mask.filter(ImageFilter.GaussianBlur(blur))
    a = ImageChops.offset(a, 0, dy).point(lambda v: int(v * alpha))
    s.putalpha(a)
    return s


def tile(top, bot, margin=64, rim=(255, 255, 255)):
    """glossy rounded-square tile; returns (image, mask)."""
    m = squircle(margin)
    img = shadow(m)
    body = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    body.paste(vgrad(top, bot), (0, 0), m)
    # soft inner light along the top edge
    gl = Image.new("L", (N, N), 0)
    ImageDraw.Draw(gl).ellipse([-N * 0.25, margin - N * 0.62, N * 1.25, N * 0.50], fill=255)
    gl = gl.filter(ImageFilter.GaussianBlur(95))
    gloss = Image.new("RGBA", (N, N), rim + (0,))
    gloss.putalpha(ImageChops.multiply(gl, m).point(lambda v: int(v * 0.30)))
    body = Image.alpha_composite(body, gloss)
    # hairline rim
    ring = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(7)))
    rimimg = Image.new("RGBA", (N, N), rim + (0,))
    top_fade = lgrad(255, 0)
    rimimg.putalpha(ImageChops.multiply(ring, top_fade).point(lambda v: int(v * 0.55)))
    body = Image.alpha_composite(body, rimimg)
    return Image.alpha_composite(img, body), m


def finish(img, glyph, gshadow=True):
    if gshadow:
        a = glyph.getchannel("A")
        sh = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        sh.putalpha(ImageChops.offset(a.filter(ImageFilter.GaussianBlur(12)), 0, 10).point(lambda v: int(v * 0.35)))
        img = Image.alpha_composite(img, sh)
    return Image.alpha_composite(img, glyph)


def line(d, pts, w, fill, round_ends=True):
    d.line(pts, fill=fill, width=w, joint="curve")
    if round_ends:
        for p in (pts[0], pts[-1]):
            d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=fill)


def rrect(d, box, r, fill):
    d.rounded_rectangle(box, radius=r, fill=fill)


def masked(src, mask):
    out = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    out.paste(src, (0, 0), mask)
    return out


WHITE = (255, 255, 255, 255)


# ----------------------------------------------------------------------------- icons
def icon_launcher():
    img, m = tile((52, 38, 40), (24, 18, 22))
    # orange glowing rim
    ring = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(15)))
    glow = Image.new("RGBA", (N, N), (255, 140, 40, 0))
    glow.putalpha(ring.filter(ImageFilter.GaussianBlur(10)).point(lambda v: min(255, int(v * 1.4))))
    img = Image.alpha_composite(img, glow)
    g = new()
    d = ImageDraw.Draw(g)
    s, gap, x0 = 168, 52, C - 168 - 26
    for i in range(2):
        for j in range(2):
            x, y = x0 + i * (s + gap), x0 + j * (s + gap)
            rrect(d, [x, y, x + s, y + s], 58, (255, 150, 40, 255))
    return finish(img, g)


def icon_files():
    img, m = tile((84, 208, 255), (8, 104, 236))
    g = new()
    d = ImageDraw.Draw(g)
    rrect(d, [236, 290, 788, 740], 64, (255, 255, 255, 245))
    d.rounded_rectangle([236, 290, 788, 392], radius=64, fill=(214, 232, 252, 255))
    d.rectangle([236, 350, 788, 392], fill=(214, 232, 252, 255))
    for i, col in enumerate(((255, 96, 88), (255, 190, 60), (60, 204, 96))):
        d.ellipse([280 + i * 58 - 18, 341 - 18, 280 + i * 58 + 18, 341 + 18], fill=col + (255,))
    d.rectangle([236, 392, 388, 740], fill=(232, 241, 252, 255))
    d.rounded_rectangle([236, 640, 388, 740], radius=64, fill=(232, 241, 252, 255))
    d.rectangle([236, 640, 300, 700], fill=(232, 241, 252, 255))
    d.line([(388, 392), (388, 740)], fill=(190, 210, 236, 255), width=6)
    for k in range(3):
        rrect(d, [270, 430 + k * 64, 354, 462 + k * 64], 16, (120, 160, 214, 255))
    for r_ in range(2):
        for c_ in range(2):
            x, y = 430 + c_ * 170, 440 + r_ * 150
            d.rounded_rectangle([x, y, x + 120, y + 100], radius=22, fill=(80, 170, 255, 255))
            d.rectangle([x, y, x + 56, y + 14], fill=(50, 130, 230, 255))
    return finish(img, g)


def folder(top, bot, glyph=None, back_scale=0.78):
    img = new()
    mask = Image.new("L", (N, N), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([96, 300, 928, 830], radius=84, fill=255)
    md.rounded_rectangle([96, 216, 470, 400], radius=70, fill=255)
    img = shadow(mask, dy=22, blur=24, alpha=0.45)
    back = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    bm = Image.new("L", (N, N), 0)
    bd = ImageDraw.Draw(bm)
    bd.rounded_rectangle([96, 300, 928, 830], radius=84, fill=255)
    bd.rounded_rectangle([96, 216, 470, 400], radius=70, fill=255)
    back.paste(vgrad(tuple(int(c * back_scale) for c in top), tuple(int(c * back_scale) for c in bot)), (0, 0), bm)
    img = Image.alpha_composite(img, back)
    fm = Image.new("L", (N, N), 0)
    ImageDraw.Draw(fm).rounded_rectangle([96, 372, 928, 846], radius=84, fill=255)
    front = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    front.paste(vgrad(top, bot), (0, 0), fm)
    hl = Image.new("RGBA", (N, N), (255, 255, 255, 0))
    ring = ImageChops.subtract(fm, fm.filter(ImageFilter.MinFilter(9)))
    hl.putalpha(ImageChops.multiply(ring, lgrad(255, 0)).point(lambda v: int(v * 0.7)))
    front = Image.alpha_composite(front, hl)
    img = Image.alpha_composite(img, front)
    if glyph:
        g = new()
        glyph(ImageDraw.Draw(g))
        img = finish(img, g, gshadow=True)
    return img


def g_lines(d):
    for k in range(3):
        rrect(d, [330, 530 + k * 70, 694, 556 + k * 70], 13, (255, 255, 255, 235))


def g_down(d):
    line(d, [(512, 500), (512, 740)], 54, WHITE)
    line(d, [(412, 650), (512, 750), (612, 650)], 54, WHITE)


def g_note(d):
    d.ellipse([360, 680, 470, 750], fill=WHITE)
    d.ellipse([560, 640, 670, 710], fill=WHITE)
    d.rectangle([448, 520, 474, 716], fill=WHITE)
    d.rectangle([648, 490, 674, 676], fill=WHITE)
    d.polygon([(448, 520), (674, 490), (674, 540), (448, 572)], fill=WHITE)


def g_pic(d):
    d.polygon([(300, 780), (440, 580), (530, 700), (610, 620), (730, 780)], fill=(255, 255, 255, 245))
    d.ellipse([590, 500, 666, 576], fill=(255, 255, 255, 245))


def g_play(d):
    d.polygon([(450, 540), (450, 760), (640, 650)], fill=WHITE)


def g_code(d):
    line(d, [(450, 540), (370, 650), (450, 760)], 40, WHITE)
    line(d, [(574, 540), (654, 650), (574, 760)], 40, WHITE)


def g_dots(d):
    for x in (380, 512, 644):
        d.ellipse([x - 30, 650 - 30, x + 30, 650 + 30], fill=WHITE)


def icon_folder_blue():
    return folder((96, 200, 255), (24, 120, 250))


def icon_home():
    return folder((255, 190, 70), (255, 120, 20))


def icon_documents():
    return folder((255, 190, 70), (255, 120, 20), g_lines)


def icon_downloads():
    return folder((40, 214, 168), (10, 150, 130), g_down)


def icon_music_folder():
    return folder((255, 96, 130), (232, 30, 84), g_note)


def icon_pictures():
    return folder((190, 110, 255), (120, 50, 230), g_pic)


def icon_videos():
    return folder((70, 170, 255), (20, 90, 240), g_play)


def icon_projects():
    return folder((40, 210, 220), (10, 140, 190), g_code)


def icon_more():
    return folder((70, 68, 80), (36, 34, 44), g_dots)


def icon_browser():
    img, m = tile((255, 176, 64), (226, 52, 110))
    g = new()
    d = ImageDraw.Draw(g)
    w = 34
    d.ellipse([C - 290, C - 290, C + 290, C + 290], outline=WHITE, width=w)
    d.ellipse([C - 126, C - 290, C + 126, C + 290], outline=WHITE, width=w - 8)
    line(d, [(C - 290, C), (C + 290, C)], w - 8, WHITE)
    for dy in (-150, 150):
        hw = math.sqrt(290 ** 2 - dy ** 2)
        line(d, [(C - hw, C + dy), (C + hw, C + dy)], w - 14, WHITE)
    return finish(img, g)


def icon_terminal():
    img, m = tile((52, 58, 92), (20, 24, 46))
    g = new()
    d = ImageDraw.Draw(g)
    line(d, [(300, 350), (480, 512), (300, 674)], 58, WHITE)
    line(d, [(540, 690), (720, 690)], 58, (255, 160, 60, 255))
    return finish(img, g)


def gear(d, cx, cy, ro, ri, teeth, hole, fill, holefill):
    pts = []
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        w = math.pi / teeth
        for da, r in ((-0.62 * w, ri), (-0.36 * w, ro), (0.36 * w, ro), (0.62 * w, ri)):
            pts.append((cx + r * math.cos(a + da), cy + r * math.sin(a + da)))
    d.polygon(pts, fill=fill)
    d.ellipse([cx - hole, cy - hole, cx + hole, cy + hole], fill=holefill)


def icon_settings():
    img, m = tile((112, 116, 128), (50, 52, 62))
    g = new()
    d = ImageDraw.Draw(g)
    gear(d, C, C, 300, 232, 10, 102, (226, 230, 238, 255), (66, 68, 78, 255))
    d.ellipse([C - 62, C - 62, C + 62, C + 62], fill=(150, 154, 166, 255))
    return finish(img, g)


def icon_photos():
    """Three overlapping translucent discs (multiply-blended) on a white tile."""
    img, m = tile((255, 255, 255), (226, 228, 236))
    discs = [((C, C - 105), (255, 96, 110)), ((C - 122, C + 108), (60, 196, 130)), ((C + 122, C + 108), (70, 140, 255))]
    base = img.convert("RGB")
    for (cx, cy), col in discs:
        lay = Image.new("RGB", (N, N), (255, 255, 255))
        ImageDraw.Draw(lay).ellipse([cx - 210, cy - 210, cx + 210, cy + 210], fill=col)
        lay = Image.composite(lay, Image.new("RGB", (N, N), (255, 255, 255)), m)
        base = ImageChops.multiply(base, lay)
    out = base.convert("RGBA")
    out.putalpha(img.getchannel("A"))
    return out


def icon_video():
    img, m = tile((44, 36, 52), (16, 12, 22))
    g = new()
    d = ImageDraw.Draw(g)
    body = masked(hgrad((255, 80, 120), (70, 120, 255)), Image.new("L", (N, N), 0))
    mk = Image.new("L", (N, N), 0)
    ImageDraw.Draw(mk).rounded_rectangle([226, 440, 798, 780], radius=40, fill=255)
    body = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    gr = hgrad((255, 150, 60), (190, 60, 255))
    gr2 = vgrad((255, 255, 255, 0), (0, 40, 255, 150))
    gr = Image.alpha_composite(gr, gr2)
    body.paste(gr, (0, 0), mk)
    g = Image.alpha_composite(g, body)
    d = ImageDraw.Draw(g)
    # striped clapper bar
    bar = new()
    bd = ImageDraw.Draw(bar)
    bd.rounded_rectangle([226, 300, 798, 410], radius=26, fill=(250, 250, 252, 255))
    for k in range(6):
        x = 226 + k * 100
        bd.polygon([(x + 30, 300), (x + 90, 300), (x + 60, 410), (x, 410)], fill=(30, 28, 38, 255))
    bm = Image.new("L", (N, N), 0)
    ImageDraw.Draw(bm).rounded_rectangle([226, 300, 798, 410], radius=26, fill=255)
    bar = masked(bar, bm)
    g = Image.alpha_composite(g, bar)
    return finish(img, g)


def icon_music():
    img, m = tile((255, 104, 132), (226, 28, 80))
    g = new()
    d = ImageDraw.Draw(g)
    d.ellipse([336, 646, 476, 750], fill=WHITE)
    d.ellipse([566, 606, 706, 710], fill=WHITE)
    d.rectangle([446, 300, 482, 704], fill=WHITE)
    d.rectangle([676, 262, 712, 664], fill=WHITE)
    d.polygon([(446, 300), (712, 262), (712, 350), (446, 392)], fill=WHITE)
    return finish(img, g)


def icon_code():
    img, m = tile((72, 160, 255), (26, 72, 226))
    g = new()
    d = ImageDraw.Draw(g)
    line(d, [(400, 330), (252, 512), (400, 694)], 62, WHITE)
    line(d, [(624, 330), (772, 512), (624, 694)], 62, WHITE)
    line(d, [(566, 290), (458, 734)], 56, (255, 255, 255, 235))
    return finish(img, g)


def icon_trash():
    mask = Image.new("L", (N, N), 0)
    md = ImageDraw.Draw(mask)
    body_poly = [(290, 340), (734, 340), (690, 850), (334, 850)]
    md.polygon(body_poly, fill=255)
    md.rounded_rectangle([250, 266, 774, 346], radius=34, fill=255)
    img = shadow(mask, dy=20, blur=22, alpha=0.45)
    body = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    bm = Image.new("L", (N, N), 0)
    ImageDraw.Draw(bm).polygon(body_poly, fill=255)
    body.paste(vgrad((210, 216, 228, 235), (150, 156, 172, 235)), (0, 0), bm)
    d = ImageDraw.Draw(body)
    for k in range(5):
        x = 352 + k * 80
        d.line([(x, 400), (x - 6 + (k - 2) * -3, 800)], fill=(110, 116, 134, 200), width=16)
    lm = Image.new("L", (N, N), 0)
    ImageDraw.Draw(lm).rounded_rectangle([250, 266, 774, 346], radius=34, fill=255)
    lid = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    lid.paste(vgrad((236, 240, 248, 255), (178, 184, 200, 255)), (0, 0), lm)
    ImageDraw.Draw(lid).rounded_rectangle([430, 214, 594, 280], radius=26, outline=(200, 206, 220, 255), width=22)
    img = Image.alpha_composite(img, body)
    img = Image.alpha_composite(img, lid)
    g = new()
    gd = ImageDraw.Draw(g)
    gd.ellipse([C - 60, 560 - 60, C + 60, 560 + 60], fill=(70, 150, 255, 235))
    gd.ellipse([C - 26, 560 - 26, C + 26, 560 + 26], fill=(210, 216, 228, 255))
    return Image.alpha_composite(img, g)


def icon_calculator():
    img, m = tile((74, 76, 86), (34, 35, 42))
    g = new()
    d = ImageDraw.Draw(g)
    rrect(d, [236, 236, 788, 372], 34, (28, 29, 34, 255))
    d.rectangle([640, 290, 744, 312], fill=(255, 150, 40, 255))
    cs, gap = 112, 28
    x0, y0 = 236, 408
    for r in range(4):
        for c in range(4):
            x, y = x0 + c * (cs + gap), y0 + r * (cs + gap)
            if c == 3:
                col = (255, 150, 40, 255)
            elif r == 0:
                col = (132, 136, 148, 255)
            else:
                col = (98, 101, 112, 255)
            rrect(d, [x, y, x + cs, y + cs], 30, col)
    return finish(img, g)


def icon_store():
    img, m = tile((148, 104, 255), (66, 48, 214))
    g = new()
    d = ImageDraw.Draw(g)
    d.arc([388, 214, 636, 560], 180, 360, fill=WHITE, width=40)
    d.polygon([(282, 410), (742, 410), (780, 790), (244, 790)], fill=WHITE)
    d.rounded_rectangle([244, 380, 780, 440], radius=26, fill=(240, 236, 255, 255))
    d.polygon([(512, 520), (610, 730), (566, 730), (512, 610), (458, 730), (414, 730)], fill=(86, 62, 226, 255))
    return finish(img, g)


def icon_editor():
    img, m = tile((255, 206, 70), (255, 126, 34))
    g = new()
    d = ImageDraw.Draw(g)
    rrect(d, [270, 214, 700, 810], 46, (255, 255, 255, 250))
    for k in range(5):
        rrect(d, [330, 320 + k * 96, 640 - (k % 2) * 90, 346 + k * 96], 13, (214, 186, 156, 255))
    pen = new()
    pd = ImageDraw.Draw(pen)
    pd.polygon([(620, 600), (700, 560), (860, 720), (800, 790), (740, 840), (640, 780)], fill=(70, 78, 98, 255))
    pd.polygon([(700, 560), (746, 520), (906, 680), (860, 720)], fill=(255, 96, 90, 255))
    pd.polygon([(620, 780), (640, 780), (740, 840), (580, 850)], fill=(255, 222, 160, 255))
    return finish(img, Image.alpha_composite(g, pen))


def icon_imageviewer():
    img, m = tile((52, 220, 196), (8, 130, 176))
    g = new()
    d = ImageDraw.Draw(g)
    d.rounded_rectangle([240, 290, 784, 734], radius=44, outline=WHITE, width=38)
    d.polygon([(296, 690), (440, 500), (540, 626), (620, 540), (738, 690)], fill=WHITE)
    d.ellipse([594, 372, 678, 456], fill=WHITE)
    return finish(img, g)


def icon_screenshot():
    img, m = tile((120, 120, 255), (56, 52, 212))
    g = new()
    d = ImageDraw.Draw(g)
    L = 120
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = C + sx * 250, C + sy * 250
            line(d, [(cx - sx * L, cy), (cx, cy), (cx, cy - sy * L)], 44, WHITE)
    d.ellipse([C - 96, C - 96, C + 96, C + 96], fill=WHITE)
    d.ellipse([C - 54, C - 54, C + 54, C + 54], fill=(70, 66, 220, 255))
    return finish(img, g)


def icon_mark():
    """The AVYX mark: a rounded orange peak with an inner notch."""
    img = new()
    d = ImageDraw.Draw(img)
    pts = [(C, 150), (900, 840), (124, 840)]
    outer = Image.new("L", (N, N), 0)
    od = ImageDraw.Draw(outer)
    od.polygon(pts, fill=255)
    od.line(pts + [pts[0]], fill=255, width=120, joint="curve")
    for p in pts:
        od.ellipse([p[0] - 60, p[1] - 60, p[0] + 60, p[1] + 60], fill=255)
    outer = outer.filter(ImageFilter.GaussianBlur(1))
    gr = vgrad((255, 188, 48), (255, 92, 24))
    sh = shadow(outer, dy=18, blur=22, alpha=0.4)
    img = Image.alpha_composite(sh, masked(gr, outer))
    inner = Image.new("L", (N, N), 0)
    idr = ImageDraw.Draw(inner)
    idr.polygon([(C, 520), (668, 820), (356, 820)], fill=255)
    idr.line([(C, 520), (668, 820), (356, 820), (C, 520)], fill=255, width=46, joint="curve")
    inner = inner.filter(ImageFilter.GaussianBlur(1))
    notch = Image.new("RGBA", (N, N), (255, 214, 120, 0))
    notch.putalpha(inner.point(lambda v: int(v * 0.85)))
    return Image.alpha_composite(img, notch)


def icon_thispc():
    img = new()
    m = Image.new("L", (N, N), 0)
    ImageDraw.Draw(m).rounded_rectangle([170, 190, 854, 700], radius=60, fill=255)
    img = shadow(m, dy=22, blur=24, alpha=0.4)
    frame = new()
    frame.paste(vgrad((246, 248, 252), (186, 192, 206)), (0, 0), m)
    img = Image.alpha_composite(img, frame)
    sm = Image.new("L", (N, N), 0)
    ImageDraw.Draw(sm).rounded_rectangle([204, 224, 820, 666], radius=34, fill=255)
    scr = new()
    scr.paste(vgrad((92, 184, 255), (22, 104, 236)), (0, 0), sm)
    img = Image.alpha_composite(img, scr)
    hl = Image.new("RGBA", (N, N), (255, 255, 255, 0))
    hm = Image.new("L", (N, N), 0)
    ImageDraw.Draw(hm).polygon([(204, 224), (620, 224), (330, 666), (204, 666)], fill=255)
    hl.putalpha(ImageChops.multiply(hm, sm).point(lambda v: int(v * 0.16)))
    img = Image.alpha_composite(img, hl)
    d = ImageDraw.Draw(img)
    d.polygon([(446, 700), (578, 700), (610, 790), (414, 790)], fill=(200, 206, 220, 255))
    d.rounded_rectangle([320, 780, 704, 830], radius=24, fill=(224, 228, 238, 255))
    return img


ICONS = {
    "avyx-launcher": icon_launcher, "avyx-files": icon_files, "folder": icon_folder_blue,
    "avyx-browser": icon_browser, "avyx-terminal": icon_terminal, "avyx-settings": icon_settings,
    "avyx-photos": icon_photos, "avyx-video": icon_video, "avyx-music": icon_music,
    "avyx-code": icon_code, "trash": icon_trash, "avyx-calculator": icon_calculator,
    "avyx-store": icon_store, "avyx-editor": icon_editor, "avyx-imageviewer": icon_imageviewer,
    "avyx-screenshot": icon_screenshot, "avyx-mark": icon_mark, "this-pc": icon_thispc,
    "folder-home": icon_home, "folder-documents": icon_documents, "folder-downloads": icon_downloads,
    "folder-music": icon_music_folder, "folder-pictures": icon_pictures, "folder-videos": icon_videos,
    "folder-projects": icon_projects, "folder-more": icon_more,
}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "icons"
    os.makedirs(out, exist_ok=True)
    only = set(sys.argv[2:])
    for name, fn in ICONS.items():
        if only and name not in only:
            continue
        im = fn().resize((256, 256), Image.LANCZOS)
        im.save(os.path.join(out, name + ".png"), optimize=True)
        print("icon", name)


if __name__ == "__main__":
    main()
