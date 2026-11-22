#!/usr/bin/env python3
"""Generate the AVYX Glass look: icon theme, window decoration (round traffic-light buttons),
and Konsole glass profile. Everything here is original work (MIT / CC0).

Run from anywhere:  python3 tools/gen_theme.py
"""
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INC = ROOT / "config" / "includes.chroot_after_packages"

# ---------------------------------------------------------------------------
# Icon theme "AVYX": rounded-square app icons with a soft glass highlight.
# ---------------------------------------------------------------------------
ICON_DIR = INC / "usr/share/icons/AVYX"
HICOLOR = INC / "usr/share/icons/hicolor/scalable/apps"


def tile(c1, c2, glyph, uid, shadow_glyph=True):
    """512x512 rounded tile with depth: soft drop shadow, 3-stop gradient, glass highlight,
    lit top edge, shaded bottom edge and a soft shadow under the glyph."""
    mid = _mix(c1, c2, 0.5)
    shade = re.sub(r"#[0-9a-fA-F]{6}", "#000000", glyph) if shadow_glyph else ""
    gshadow = f'<g opacity=".22" transform="translate(0 9)">{shade}</g>' if shadow_glyph else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="bg{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{c1}"/><stop offset=".5" stop-color="{mid}"/><stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <linearGradient id="hl{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity=".40"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="rim{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity=".75"/><stop offset=".35" stop-color="#ffffff" stop-opacity=".10"/>
      <stop offset=".75" stop-color="#000000" stop-opacity=".05"/><stop offset="1" stop-color="#000000" stop-opacity=".30"/>
    </linearGradient>
  </defs>
  <rect x="30" y="40" width="452" height="456" rx="104" fill="#000" fill-opacity=".07"/>
  <rect x="34" y="34" width="444" height="456" rx="104" fill="#000" fill-opacity=".10"/>
  <rect x="38" y="30" width="436" height="454" rx="102" fill="#000" fill-opacity=".14"/>
  <rect x="24" y="22" width="464" height="464" rx="104" fill="url(#bg{uid})"/>
  <path d="M24 126 A104 104 0 0 1 128 22 H384 A104 104 0 0 1 488 126 V212 Q256 282 24 212 Z" fill="url(#hl{uid})"/>
  <rect x="26" y="24" width="460" height="460" rx="102" fill="none" stroke="url(#rim{uid})" stroke-width="4"/>
  {gshadow}
  {glyph}
</svg>
"""


def _mix(a, b, t):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def gear(cx, cy, r_out, r_in, r_hole, teeth=8):
    pts = []
    step = 2 * math.pi / teeth
    for i in range(teeth):
        a = i * step
        for da, r in ((-0.30, r_in), (-0.17, r_out), (0.17, r_out), (0.30, r_in)):
            ang = a + da * step * 1.6
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    d += f" M{cx - r_hole},{cy} a{r_hole},{r_hole} 0 1,0 {2 * r_hole},0 a{r_hole},{r_hole} 0 1,0 {-2 * r_hole},0 Z"
    return f'<path d="{d}" fill="#ffffff" fill-opacity=".95" fill-rule="evenodd"/>'


GLYPH = {
    "files": """
  <path d="M96 176 a28 28 0 0 1 28-28 h86 l34 36 h144 a28 28 0 0 1 28 28 v26 H96 z" fill="#ffffff" fill-opacity=".72"/>
  <path d="M96 232 a28 28 0 0 1 28-28 h264 a28 28 0 0 1 28 28 v128 a28 28 0 0 1 -28 28 H124 a28 28 0 0 1 -28-28 z" fill="#ffffff" fill-opacity=".96"/>""",
    "terminal": """
  <path d="M150 188 L262 258 L150 328" fill="none" stroke="#7df3ff" stroke-width="38" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M296 340 H376" fill="none" stroke="#c27bff" stroke-width="38" stroke-linecap="round"/>""",
    "editor": """
  <rect x="136" y="92" width="240" height="328" rx="30" fill="#ffffff" fill-opacity=".97"/>
  <rect x="176" y="156" width="160" height="22" rx="11" fill="#ff9a55"/>
  <rect x="176" y="206" width="160" height="22" rx="11" fill="#ffc07a"/>
  <rect x="176" y="256" width="110" height="22" rx="11" fill="#ffc07a"/>
  <rect x="176" y="306" width="140" height="22" rx="11" fill="#ffc07a"/>""",
    "images": """
  <rect x="88" y="120" width="336" height="272" rx="40" fill="#ffffff" fill-opacity=".96"/>
  <circle cx="352" cy="190" r="32" fill="#ffd36b"/>
  <path d="M112 392 L226 252 L292 330 L336 280 L400 392 Z" fill="#1fa0c8"/>
  <path d="M226 252 L292 330 L226 392 L112 392 Z" fill="#6ef0c2" fill-opacity=".9"/>""",
    "settings": gear(256, 256, 150, 118, 52),
    "installer": """
  <g fill="none" stroke="#ffffff" stroke-width="38" stroke-linecap="round" stroke-linejoin="round">
    <path d="M118 296 L256 112 L394 296" stroke-opacity=".98"/>
    <path d="M118 196 L256 392 L394 196" stroke-opacity=".72"/>
  </g>""",
    "launchpad": """
  <g>
    <rect x="108" y="108" width="82" height="82" rx="22" fill="#ff7a8a"/><rect x="215" y="108" width="82" height="82" rx="22" fill="#ffc66b"/><rect x="322" y="108" width="82" height="82" rx="22" fill="#7be0a0"/>
    <rect x="108" y="215" width="82" height="82" rx="22" fill="#6cc8ff"/><rect x="215" y="215" width="82" height="82" rx="22" fill="#b58cff"/><rect x="322" y="215" width="82" height="82" rx="22" fill="#ff8fd0"/>
    <rect x="108" y="322" width="82" height="82" rx="22" fill="#7df3ff"/><rect x="215" y="322" width="82" height="82" rx="22" fill="#a9e86a"/><rect x="322" y="322" width="82" height="82" rx="22" fill="#ffffff" fill-opacity=".92"/>
  </g>""",
    "calc": """
  <rect x="108" y="96" width="296" height="88" rx="24" fill="#7df3ff" fill-opacity=".9"/>
  <g fill="#ffffff" fill-opacity=".92">
    <circle cx="150" cy="250" r="30"/><circle cx="238" cy="250" r="30"/><circle cx="326" cy="250" r="30"/><circle cx="388" cy="250" r="0"/>
    <circle cx="150" cy="330" r="30"/><circle cx="238" cy="330" r="30"/><circle cx="326" cy="330" r="30"/>
    <circle cx="150" cy="410" r="30"/><circle cx="238" cy="410" r="30"/>
  </g>
  <rect x="296" y="380" width="60" height="60" rx="20" fill="#c27bff"/>""",
    "shot": """
  <g fill="none" stroke="#ffffff" stroke-width="30" stroke-linecap="round" stroke-linejoin="round">
    <path d="M112 196 V132 a20 20 0 0 1 20-20 H196"/><path d="M316 112 H380 a20 20 0 0 1 20 20 V196"/>
    <path d="M400 316 V380 a20 20 0 0 1 -20 20 H316"/><path d="M196 400 H132 a20 20 0 0 1 -20-20 V316"/>
  </g>
  <circle cx="256" cy="256" r="40" fill="#ffffff" fill-opacity=".92"/>""",
}

TILES = {
    "files": ("#63ccff", "#3566ec", ["system-file-manager", "org.kde.dolphin", "dolphin"]),
    "terminal": ("#3c4262", "#0f1124", ["utilities-terminal", "org.kde.konsole", "konsole"]),
    "editor": ("#ffd56e", "#ff7f4a", ["org.kde.kate", "kate", "accessories-text-editor", "org.kde.kwrite", "kwrite"]),
    "images": ("#7af2c8", "#1f8fd0", ["org.kde.gwenview", "gwenview", "viewimage"]),
    "settings": ("#a7b0d2", "#565e84", ["preferences-system", "systemsettings", "org.kde.systemsettings"]),
    "installer": ("#5667f0", "#9a5bff", ["avyx-installer"]),
    "launchpad": ("#59618a", "#232842", ["avyx-launchpad", "org.kde.plasma.kickerdash", "view-app-grid"]),
    "calc": ("#343a5e", "#14172c", ["accessories-calculator", "org.kde.kcalc", "kcalc"]),
    "shot": ("#ff82bd", "#ff4f6d", ["org.kde.spectacle", "spectacle"]),
}

MENU_MARK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7df3ff"/><stop offset=".55" stop-color="#8d9bff"/><stop offset="1" stop-color="#c27bff"/></linearGradient>
    <linearGradient id="g2" x1="1" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c27bff"/><stop offset=".5" stop-color="#8d9bff"/><stop offset="1" stop-color="#7df3ff"/></linearGradient>
  </defs>
  <g fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="46">
    <path d="M78 262 L200 72 L322 262" stroke="url(#g)"/><path d="M78 138 L200 328 L322 138" stroke="url(#g2)" stroke-opacity=".85"/>
  </g>
</svg>
"""

TRASH_EMPTY = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs><linearGradient id="t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity=".55"/><stop offset="1" stop-color="#cfd8ff" stop-opacity=".18"/></linearGradient></defs>
  <path d="M150 190 H362 L346 420 a30 30 0 0 1 -30 28 H196 a30 30 0 0 1 -30-28 Z" fill="url(#t)" stroke="#ffffff" stroke-opacity=".9" stroke-width="14" stroke-linejoin="round"/>
  <path d="M120 150 H392" stroke="#ffffff" stroke-width="26" stroke-linecap="round"/>
  <path d="M206 142 V120 a16 16 0 0 1 16-16 H290 a16 16 0 0 1 16 16 V142" fill="none" stroke="#ffffff" stroke-width="22" stroke-linecap="round"/>
  <path d="M214 232 V404 M256 232 V404 M298 232 V404" stroke="#ffffff" stroke-opacity=".7" stroke-width="14" stroke-linecap="round"/>
</svg>
"""
TRASH_FULL = TRASH_EMPTY.replace(
    "</svg>",
    '  <path d="M190 190 L222 120 L270 150 L300 96 L338 190 Z" fill="#ffffff" fill-opacity=".92"/>\n</svg>',
)

INDEX = """[Icon Theme]
Name=AVYX
Comment=AVYX Glass icon theme (original artwork)
Inherits=breeze-dark,breeze,hicolor
Directories=scalable/apps,scalable/places

[scalable/apps]
Size=128
MinSize=8
MaxSize=1024
Type=Scalable
Context=Applications

[scalable/places]
Size=128
MinSize=8
MaxSize=1024
Type=Scalable
Context=Places
"""


def write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def build_icons():
    write(ICON_DIR / "index.theme", INDEX)
    n = 0
    for uid, (key, (c1, c2, names)) in enumerate(TILES.items()):
        svg = tile(c1, c2, GLYPH[key], uid, shadow_glyph=(key != "terminal"))
        for name in names:
            write(ICON_DIR / "scalable/apps" / f"{name}.svg", svg)
            n += 1
    write(ICON_DIR / "scalable/apps/avyx-menu.svg", MENU_MARK)
    write(ICON_DIR / "scalable/places/user-trash.svg", TRASH_EMPTY)
    write(ICON_DIR / "scalable/places/user-trash-full.svg", TRASH_FULL)
    # brand-specific names also go to hicolor so they resolve whatever icon theme a user picks
    write(HICOLOR / "avyx-installer.svg", tile(*TILES["installer"][:2], GLYPH["installer"], 99))
    write(HICOLOR / "avyx-menu.svg", MENU_MARK)
    print(f"icons: {n} app aliases + menu mark + trash")


# ---------------------------------------------------------------------------
# Window decoration (Aurorae SVG theme): round red/amber/green buttons at the left.
# ---------------------------------------------------------------------------
AUR = INC / "usr/share/aurorae/themes/AVYX"

TOP_H = 34   # 7 + 20 + 7, must match the rc file
R = 11       # corner radius of the title bar
PAD = 18     # shadow extent left/right/top
PADB = 26    # shadow extent at the bottom (offset shadow)
BORDER = 2


def deco_svg():
    W_C = PAD + R + 1            # corner element width
    H_T = PAD + TOP_H            # top element height
    H_B = BORDER + PADB          # bottom element height
    W_S = PAD + BORDER           # left/right strip width
    cx = PAD + R                 # corner arc centre (x and y)

    def frame(pre, t0, t1, solid, a, ox, oy):
        """All nine elements of one state, drawn at canvas offset (ox, oy)."""
        g = pre
        defs = f"""
    <linearGradient id="{g}-t" gradientUnits="userSpaceOnUse" x1="0" y1="{oy + PAD}" x2="0" y2="{oy + H_T}">
      <stop offset="0" stop-color="{t0}"/><stop offset="1" stop-color="{t1}"/></linearGradient>
    <linearGradient id="{g}-sl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="{a}"/></linearGradient>
    <linearGradient id="{g}-sr" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="{a}"/></linearGradient>
    <linearGradient id="{g}-st" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="{a}"/></linearGradient>
    <linearGradient id="{g}-sb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="{a}"/><stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient>
    <radialGradient id="{g}-rc" gradientUnits="userSpaceOnUse" r="{cx}">
      <stop offset="{R / cx:.3f}" stop-color="#000" stop-opacity="{a}"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
    <radialGradient id="{g}-rbl" gradientUnits="userSpaceOnUse" cx="{ox + PAD}" cy="{oy + 60 + BORDER}" r="{PAD}" gradientTransform="translate({ox + PAD} {oy + 60 + BORDER}) scale(1 {PADB / PAD:.4f}) translate({-(ox + PAD)} {-(oy + 60 + BORDER)})">
      <stop offset="0" stop-color="#000" stop-opacity="{a}"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
    <radialGradient id="{g}-rbr" gradientUnits="userSpaceOnUse" cx="{ox + 100 + BORDER}" cy="{oy + 60 + BORDER}" r="{PAD}" gradientTransform="translate({ox + 100 + BORDER} {oy + 60 + BORDER}) scale(1 {PADB / PAD:.4f}) translate({-(ox + 100 + BORDER)} {-(oy + 60 + BORDER)})">
      <stop offset="0" stop-color="#000" stop-opacity="{a}"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>"""
        # --- top row (y = oy .. oy+H_T)
        tl_cx, tl_cy = ox + cx, oy + cx
        tr_x0 = ox + 100
        trcx = tr_x0 + (W_C - cx)   # arc centre of the right corner
        els = f"""
  <g id="{pre}-topleft">
    <rect x="{ox}" y="{oy}" width="{W_C}" height="{H_T}" fill="none"/>
    <rect x="{ox}" y="{oy + cx}" width="{PAD}" height="{H_T - cx}" fill="url(#{g}-sl)"/>
    <rect x="{ox + cx}" y="{oy}" width="{W_C - cx}" height="{PAD}" fill="url(#{g}-st)"/>
    <path d="M{ox} {oy} H{ox + cx} V{oy + cx} H{ox} Z" fill="url(#{g}-rc)" transform="translate(0 0)"/>
    <path d="M{ox + PAD} {oy + H_T} V{oy + PAD + R} A{R} {R} 0 0 1 {ox + PAD + R} {oy + PAD} H{ox + W_C} V{oy + H_T} Z" fill="url(#{g}-t)"/>
  </g>
  <g id="{pre}-top">
    <rect x="{ox + 40}" y="{oy}" width="12" height="{PAD}" fill="url(#{g}-st)"/>
    <rect x="{ox + 40}" y="{oy + PAD}" width="12" height="{TOP_H}" fill="url(#{g}-t)"/>
  </g>
  <g id="{pre}-topright">
    <rect x="{tr_x0}" y="{oy}" width="{W_C}" height="{H_T}" fill="none"/>
    <rect x="{tr_x0 + W_C - PAD}" y="{oy + cx}" width="{PAD}" height="{H_T - cx}" fill="url(#{g}-sr)"/>
    <rect x="{tr_x0}" y="{oy}" width="{W_C - cx}" height="{PAD}" fill="url(#{g}-st)"/>
    <path d="M{trcx} {oy} H{tr_x0 + W_C} V{oy + cx} H{trcx} Z" fill="url(#{g}-rcr)"/>
    <path d="M{tr_x0} {oy + H_T} V{oy + PAD} H{trcx} A{R} {R} 0 0 1 {tr_x0 + W_C - PAD} {oy + PAD + R} V{oy + H_T} Z" fill="url(#{g}-t)"/>
  </g>
  <g id="{pre}-left">
    <rect x="{ox + 160}" y="{oy}" width="{PAD}" height="20" fill="url(#{g}-sl)"/>
    <rect x="{ox + 160 + PAD}" y="{oy}" width="{BORDER}" height="20" fill="{solid}"/>
  </g>
  <g id="{pre}-right">
    <rect x="{ox + 200}" y="{oy}" width="{BORDER}" height="20" fill="{solid}"/>
    <rect x="{ox + 200 + BORDER}" y="{oy}" width="{PAD}" height="20" fill="url(#{g}-sr)"/>
  </g>
  <g id="{pre}-bottom">
    <rect x="{ox + 240}" y="{oy}" width="20" height="{BORDER}" fill="{solid}"/>
    <rect x="{ox + 240}" y="{oy + BORDER}" width="20" height="{PADB}" fill="url(#{g}-sb)"/>
  </g>
  <g id="{pre}-bottomleft">
    <rect x="{ox}" y="{oy + 60}" width="{W_S}" height="{H_B}" fill="none"/>
    <rect x="{ox}" y="{oy + 60}" width="{PAD}" height="{H_B}" fill="url(#{g}-rbl)"/>
    <rect x="{ox + PAD}" y="{oy + 60 + BORDER}" width="{BORDER}" height="{PADB}" fill="url(#{g}-sb)"/>
    <rect x="{ox + PAD}" y="{oy + 60}" width="{BORDER}" height="{BORDER}" fill="{solid}"/>
  </g>
  <g id="{pre}-bottomright">
    <rect x="{ox + 100}" y="{oy + 60}" width="{W_S}" height="{H_B}" fill="none"/>
    <rect x="{ox + 100 + BORDER}" y="{oy + 60}" width="{PAD}" height="{H_B}" fill="url(#{g}-rbr)"/>
    <rect x="{ox + 100}" y="{oy + 60 + BORDER}" width="{BORDER}" height="{PADB}" fill="url(#{g}-sb)"/>
    <rect x="{ox + 100}" y="{oy + 60}" width="{BORDER}" height="{BORDER}" fill="{solid}"/>
  </g>
  <rect id="{pre}-center" x="{ox + 300}" y="{oy}" width="10" height="10" fill="{solid}"/>"""
        # radial gradients of the right corner need their own centre
        defs += f"""
    <radialGradient id="{g}-rcr" gradientUnits="userSpaceOnUse" cx="{trcx}" cy="{oy + cx}" r="{cx}">
      <stop offset="{R / cx:.3f}" stop-color="#000" stop-opacity="{a}"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>"""
        defs = defs.replace(f'<radialGradient id="{g}-rc" gradientUnits="userSpaceOnUse" r="{cx}">',
                            f'<radialGradient id="{g}-rc" gradientUnits="userSpaceOnUse" cx="{tl_cx}" cy="{tl_cy}" r="{cx}">')
        return defs, els

    d1, e1 = frame("decoration", "#2e3454", "#242a46", "#242a46", 0.30, 0, 0)
    d2, e2 = frame("decoration-inactive", "#272c48", "#22273f", "#22273f", 0.14, 0, 130)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="420" height="260" viewBox="0 0 420 260"><defs>', d1, d2, "</defs>", e1, e2,
             '<rect id="decoration-maximized-center" x="330" y="0" width="10" height="10" fill="#272c48"/>',
             '<rect id="decoration-maximized-inactive-center" x="350" y="0" width="10" height="10" fill="#22273f"/>',
             "</svg>"]
    return "\n".join(parts)


def button_svg(kind, c1, c2):
    ink = {"close": "#5a0f1c", "minimize": "#5c3d00", "maximize": "#0a4a28", "restore": "#0a4a28"}[kind]
    glyph = {
        "close": f'<path d="M5.2 5.2 L10.8 10.8 M10.8 5.2 L5.2 10.8" stroke="{ink}" stroke-width="1.7" stroke-linecap="round"/>',
        "minimize": f'<path d="M4.6 8 H11.4" stroke="{ink}" stroke-width="1.7" stroke-linecap="round"/>',
        "maximize": f'<path d="M8 4.6 V11.4 M4.6 8 H11.4" stroke="{ink}" stroke-width="1.7" stroke-linecap="round"/>',
        "restore": f'<rect x="5" y="5" width="6" height="6" rx="1.2" fill="none" stroke="{ink}" stroke-width="1.5"/>',
    }[kind]

    def dot(i, x, fill, glyph_svg="", stroke="#ffffff", sop=".35", extra=""):
        return (f'<g id="{i}" transform="translate({x} 0)"><circle cx="8" cy="8" r="8" fill="{fill}"/>'
                f'<circle cx="8" cy="8" r="7.5" fill="none" stroke="{stroke}" stroke-opacity="{sop}" stroke-width="1"/>'
                f'{extra}{glyph_svg}</g>')

    gloss = '<ellipse cx="8" cy="3.6" rx="5" ry="3" fill="#ffffff" fill-opacity=".28"/>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="100" height="16" viewBox="0 0 100 16">
  <defs>
    <linearGradient id="c" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
    <linearGradient id="p" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c2}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
  </defs>
  {dot("active-center", 0, "url(#c)", extra=gloss)}
  {dot("hover-center", 20, "url(#c)", glyph, extra=gloss)}
  {dot("pressed-center", 40, "url(#p)", glyph)}
  {dot("inactive-center", 60, "#4a4f6c", sop=".12")}
  {dot("deactivated-center", 80, "#3a3e58", sop=".06")}
</svg>
"""


RC = """[General]
TitleAlignment=Center
TitleVerticalAlignment=Center
Animation=120
ActiveTextColor=236,239,255,255
InactiveTextColor=130,137,168,255
UseTextShadow=false
LeftButtons=XIA
RightButtons=
Shadow=true
DecorationPositon=0

[Layout]
BorderLeft=2
BorderRight=2
BorderBottom=2
BorderTop=0
TitleEdgeTop=7
TitleEdgeBottom=7
TitleEdgeLeft=14
TitleEdgeRight=14
TitleEdgeTopMaximized=7
TitleEdgeBottomMaximized=7
TitleEdgeLeftMaximized=14
TitleEdgeRightMaximized=14
TitleBorderLeft=8
TitleBorderRight=8
TitleHeight=20
ButtonWidth=14
ButtonWidthMinimize=14
ButtonWidthMaximizeRestore=14
ButtonWidthClose=14
ButtonHeight=14
ButtonSpacing=8
ButtonMarginTop=3
ExplicitButtonSpacer=10
PaddingTop=18
PaddingBottom=26
PaddingRight=18
PaddingLeft=18
"""

META = """[Desktop Entry]
Name=AVYX Glass
Comment=AVYX window decoration with round traffic-light buttons
X-KDE-PluginInfo-Name=AVYX
X-KDE-PluginInfo-Author=AVYX
X-KDE-PluginInfo-Version=0.1
X-KDE-PluginInfo-License=MIT
"""


def build_decoration():
    write(AUR / "metadata.desktop", META)
    write(AUR / "AVYXrc", RC)
    write(AUR / "decoration.svg", deco_svg())
    write(AUR / "close.svg", button_svg("close", "#ff8591", "#ec3f57"))
    write(AUR / "minimize.svg", button_svg("minimize", "#ffdc86", "#f0a323"))
    write(AUR / "maximize.svg", button_svg("maximize", "#6be69b", "#1fb765"))
    write(AUR / "restore.svg", button_svg("restore", "#6be69b", "#1fb765"))
    print("decoration: AVYX aurorae theme")


# ---------------------------------------------------------------------------
# Konsole: translucent, blurred terminal ("glass") as the default profile.
# ---------------------------------------------------------------------------
KONSOLE = INC / "usr/share/konsole"


def build_konsole():
    def c(name, rgb, faint=None, intense=None):
        s = f"[{name}]\nColor={rgb}\n\n"
        return s

    pal = {
        "Background": "14,16,30", "Foreground": "232,235,250",
        "Color0": "36,40,64", "Color1": "255,107,129", "Color2": "94,230,160", "Color3": "255,201,107",
        "Color4": "125,160,255", "Color5": "194,123,255", "Color6": "125,243,255", "Color7": "208,213,235",
    }
    out = []
    for k, v in pal.items():
        out.append(f"[{k}]\nColor={v}\n")
        out.append(f"[{k}Intense]\nColor={v}\n")
        out.append(f"[{k}Faint]\nColor={v}\n")
    out.append("[General]\nBlur=true\nColorRandomization=false\nDescription=AVYX Glass\nOpacity=0.72\nWallpaper=\n")
    write(KONSOLE / "AVYX.colorscheme", "\n".join(out))
    write(KONSOLE / "AVYX.profile",
          "[Appearance]\nColorScheme=AVYX\n\n[General]\nName=AVYX\nParent=FALLBACK/\nTerminalMargin=10\n\n"
          "[Scrolling]\nScrollBarPosition=2\n")
    write(INC / "etc/xdg/konsolerc", "[Desktop Entry]\nDefaultProfile=AVYX.profile\n")
    print("konsole: AVYX glass profile")


# ---------------------------------------------------------------------------
# Plasma theme "AVYX Glass": frosted, rounded panels and popups. Only the backgrounds are
# replaced; everything else falls back to Plasma's default theme.
# ---------------------------------------------------------------------------
PTHEME = INC / "usr/share/plasma/desktoptheme/avyx-glass"


def frame_svg(R, m_tb, m_lr, fill="#dfe6ff", op=0.17, edge=0.42, edge_soft=0.14):
    """FrameSvg 9-slice (names and hint conventions follow Plasma's own themes)."""
    C = 32  # stretchable middle size
    W = 2 * R + C

    def slices(ox, oy, pre, body):
        e = []
        t = lambda n, x, y, inner: f'<g id="{pre}{n}" transform="translate({ox + x},{oy + y})">{inner}</g>'
        e.append(t("topleft", 0, 0, body("tl")))
        e.append(t("top", R, 0, body("t")))
        e.append(t("topright", R + C, 0, body("tr")))
        e.append(t("left", 0, R, body("l")))
        e.append(t("center", R, R, body("c")))
        e.append(t("right", R + C, R, body("r")))
        e.append(t("bottomleft", 0, R + C, body("bl")))
        e.append(t("bottom", R, R + C, body("b")))
        e.append(t("bottomright", R + C, R + C, body("br")))
        return "\n  ".join(e)

    def glass(k):
        f = f'fill="{fill}" fill-opacity="{op}"'
        hi = f'fill="none" stroke="#ffffff" stroke-opacity="{edge}" stroke-width="1"'
        lo = f'fill="none" stroke="#ffffff" stroke-opacity="{edge_soft}" stroke-width="1"'
        r = R - 0.5
        return {
            "tl": f'<path d="M0 {R} A{R} {R} 0 0 1 {R} 0 V{R} Z" {f}/><path d="M0.5 {R} A{r} {r} 0 0 1 {R} 0.5" {hi}/>',
            "t": f'<rect width="{C}" height="{R}" {f}/><rect width="{C}" height="1" fill="#fff" fill-opacity="{edge}"/>',
            "tr": f'<path d="M0 0 A{R} {R} 0 0 1 {R} {R} H0 Z" {f}/><path d="M0 0.5 A{r} {r} 0 0 1 {R - 0.5} {R}" {hi}/>',
            "l": f'<rect width="{R}" height="{C}" {f}/><rect width="1" height="{C}" fill="#fff" fill-opacity="{edge}"/>',
            "c": f'<rect width="{C}" height="{C}" {f}/>',
            "r": f'<rect width="{R}" height="{C}" {f}/><rect x="{R - 1}" width="1" height="{C}" fill="#fff" fill-opacity="{edge}"/>',
            "bl": f'<path d="M0 0 H{R} V{R} A{R} {R} 0 0 1 0 0 Z" {f}/><path d="M0.5 0 A{r} {r} 0 0 0 {R} {R - 0.5}" {lo}/>',
            "b": f'<rect width="{C}" height="{R}" {f}/><rect y="{R - 1}" width="{C}" height="1" fill="#fff" fill-opacity="{edge_soft}"/>',
            "br": f'<path d="M{R} 0 A{R} {R} 0 0 1 0 {R} V0 Z" {f}/><path d="M{R} 0 A{r} {r} 0 0 1 0 {R - 0.5}" fill="none" stroke="#fff" stroke-opacity="{edge_soft}" stroke-width="1"/>',
        }[k]

    def mask(k):
        f = 'fill="#000"'
        return {
            "tl": f'<path d="M0 {R} A{R} {R} 0 0 1 {R} 0 V{R} Z" {f}/>',
            "t": f'<rect width="{C}" height="{R}" {f}/>',
            "tr": f'<path d="M0 0 A{R} {R} 0 0 1 {R} {R} H0 Z" {f}/>',
            "l": f'<rect width="{R}" height="{C}" {f}/>',
            "c": f'<rect width="{C}" height="{C}" {f}/>',
            "r": f'<rect width="{R}" height="{C}" {f}/>',
            "bl": f'<path d="M0 0 H{R} V{R} A{R} {R} 0 0 1 0 0 Z" {f}/>',
            "b": f'<rect width="{C}" height="{R}" {f}/>',
            "br": f'<path d="M{R} 0 A{R} {R} 0 0 1 0 {R} V0 Z" {f}/>',
        }[k]

    tiny = "0.00000001"
    hints = f"""
  <rect id="hint-tile-center" width="5" height="5" x="0" y="{W + 4}" fill="#ff6600"/>
  <rect id="hint-top-margin" width="4" height="{m_tb}" x="20" y="{W + 4}" fill="#ff00ff"/>
  <rect id="hint-bottom-margin" width="4" height="{m_tb}" x="30" y="{W + 4}" fill="#ff00ff"/>
  <rect id="hint-left-margin" width="{m_lr}" height="4" x="40" y="{W + 4}" fill="#ff00ff"/>
  <rect id="hint-right-margin" width="{m_lr}" height="4" x="60" y="{W + 4}" fill="#ff00ff"/>
  <rect id="hint-top-inset" width="4" height="{tiny}" x="80" y="{W + 4}" fill="#00ff00"/>
  <rect id="hint-bottom-inset" width="4" height="{tiny}" x="90" y="{W + 4}" fill="#00ff00"/>
  <rect id="hint-left-inset" width="{tiny}" height="4" x="100" y="{W + 4}" fill="#00ff00"/>
  <rect id="hint-right-inset" width="{tiny}" height="4" x="110" y="{W + 4}" fill="#00ff00"/>"""
    g, m = glass, mask
    body = slices(0, 0, "", lambda k: g(k))
    masks = slices(W + 20, 0, "mask-", lambda k: m(k)).replace('id="mask-center"', 'id="mask-center"')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{2 * W + 40}" height="{W + 12}" viewBox="0 0 {2 * W + 40} {W + 12}">\n  '
            + body + "\n  " + masks + hints + "\n</svg>\n")


def build_plasma_theme():
    write(PTHEME / "metadata.json", """{
    "KPackageStructure": "Plasma/Theme",
    "KPlugin": {
        "Authors": [{ "Name": "AVYX" }],
        "Description": "Frosted glass panels and popups",
        "Id": "avyx-glass",
        "License": "MIT",
        "Name": "AVYX Glass",
        "Version": "0.1"
    }
}
""")
    panel = frame_svg(R=20, m_tb=6, m_lr=12)
    dlg = frame_svg(R=16, m_tb=10, m_lr=10, op=0.30, edge=0.35)
    for sub in ("widgets", "translucent/widgets"):
        write(PTHEME / sub / "panel-background.svg", panel)
    for sub in ("dialogs", "translucent/dialogs"):
        write(PTHEME / sub / "background.svg", dlg)
    write(INC / "etc/xdg/plasmarc", "[Theme]\nname=avyx-glass\n")
    print("plasma theme: avyx-glass")


if __name__ == "__main__":
    build_icons()
    build_decoration()
    build_konsole()
    build_plasma_theme()
