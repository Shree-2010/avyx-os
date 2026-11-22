#!/usr/bin/env python3
"""Generate the AVYX Glass look: icon theme, window decoration (round traffic-light buttons),
and Konsole glass profile. Everything here is original work (MIT / CC0).

Run from anywhere:  python3 tools/gen_theme.py
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INC = ROOT / "config" / "includes.chroot_after_packages"

# ---------------------------------------------------------------------------
# Icon theme "AVYX": rounded-square app icons with a soft glass highlight.
# ---------------------------------------------------------------------------
ICON_DIR = INC / "usr/share/icons/AVYX"
HICOLOR = INC / "usr/share/icons/hicolor/scalable/apps"


def tile(c1, c2, glyph, uid):
    """512x512 rounded tile: vertical gradient, glass highlight on the upper half, hairline edge."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="bg{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <linearGradient id="hl{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity=".42"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="cp{uid}"><rect x="16" y="16" width="480" height="480" rx="112"/></clipPath>
  </defs>
  <rect x="16" y="16" width="480" height="480" rx="112" fill="url(#bg{uid})"/>
  <g clip-path="url(#cp{uid})"><ellipse cx="256" cy="-40" rx="400" ry="300" fill="url(#hl{uid})"/></g>
  <rect x="17.5" y="17.5" width="477" height="477" rx="110.5" fill="none" stroke="#ffffff" stroke-opacity=".28" stroke-width="3"/>
  {glyph}
</svg>
"""


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
        svg = tile(c1, c2, GLYPH[key], uid)
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
R = 11       # corner radius


def deco_svg():
    def grad(uid, a, b, h=TOP_H):
        return (f'<linearGradient id="{uid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{h}">'
                f'<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>')

    def frame(prefix, fill_top, solid):
        # canvas layout: top row y=0..34 ; edges below at y=40
        return f"""
  <path id="{prefix}-topleft" d="M0 {TOP_H} V{R} A{R} {R} 0 0 1 {R} 0 H{R + 1} V{TOP_H} Z" fill="{fill_top}"/>
  <rect id="{prefix}-top" x="20" y="0" width="12" height="{TOP_H}" fill="{fill_top}"/>
  <path id="{prefix}-topright" d="M40 0 H41 A{R} {R} 0 0 1 {41 + R} {R} V{TOP_H} H40 Z" fill="{fill_top}"/>
  <rect id="{prefix}-left" x="0" y="40" width="2" height="20" fill="{solid}"/>
  <rect id="{prefix}-right" x="10" y="40" width="2" height="20" fill="{solid}"/>
  <rect id="{prefix}-bottom" x="20" y="40" width="20" height="2" fill="{solid}"/>
  <rect id="{prefix}-bottomleft" x="44" y="40" width="2" height="2" fill="{solid}"/>
  <rect id="{prefix}-bottomright" x="50" y="40" width="2" height="2" fill="{solid}"/>
  <rect id="{prefix}-center" x="60" y="40" width="10" height="10" fill="{solid}"/>"""

    # topright: shift geometry so the arc ends at the element's right edge
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="80" height="64" viewBox="0 0 80 64"><defs>',
             grad("ga", "#2e3454", "#242a46"), grad("gi", "#272c48", "#22273f"), "</defs>"]
    parts.append(frame("decoration", "url(#ga)", "#242a46"))
    parts.append(frame("decoration-inactive", "url(#gi)", "#22273f"))
    parts.append('<rect id="decoration-maximized-center" x="60" y="52" width="10" height="10" fill="#272c48"/>')
    parts.append('<rect id="decoration-maximized-inactive-center" x="72" y="52" width="6" height="6" fill="#22273f"/>')
    parts.append("</svg>")
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
Shadow=false
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
PaddingTop=0
PaddingBottom=0
PaddingRight=0
PaddingLeft=0
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


if __name__ == "__main__":
    build_icons()
    build_decoration()
    build_konsole()
