#!/usr/bin/env python3
"""Backglass (the lit art panel above a pinball table) for Kaiju Siege: Manhattan.
Drawn as pixel art at 320x360 and scaled 3x -> docs/backglass.png"""
import math, os, random, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from font import GLYPHS

W, H, S = 320, 360, 3
img = Image.new('RGB', (W, H), (0, 0, 0))
d = ImageDraw.Draw(img)
rnd = random.Random(21)

def C(r, g, b):
    return (r * 36, g * 36, b * 36)

def glyph_text(s, x, y, scale, fill_fn, outline=None, shadow=None):
    """fill_fn(row) -> color, so letters can get a vertical gradient"""
    def plot(ox, oy, colfn):
        cx = x
        for ch in s:
            g = GLYPHS.get(ch, GLYPHS[' '])
            for ry, row in enumerate(g):
                for rx, b in enumerate(row):
                    if b == '1':
                        d.rectangle((cx + rx * scale + ox, y + ry * scale + oy,
                                     cx + rx * scale + scale - 1 + ox, y + ry * scale + scale - 1 + oy), fill=colfn(ry))
            cx += 6 * scale
    if shadow:
        plot(scale, scale, lambda r: shadow)
    if outline:
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            plot(ox * 2, oy * 2, lambda r: outline)
    plot(0, 0, fill_fn)

def text_w(s, scale):
    return len(s) * 6 * scale - scale

# ---- sky
bands = [C(0, 0, 1), C(0, 0, 2), C(1, 0, 2), C(1, 0, 3), C(2, 0, 3), C(3, 1, 3), C(4, 1, 2)]
for i, col in enumerate(bands):
    d.rectangle((0, 40 + i * 30, W, 40 + i * 30 + 29), fill=col)
d.rectangle((0, 0, W, 40), fill=C(0, 0, 1))
for _ in range(90):
    x, y = rnd.randrange(W), rnd.randrange(30, 170)
    d.point((x, y), fill=C(6, 6, 7) if rnd.random() < 0.3 else C(3, 3, 5))

# ---- moon behind the kaiju
d.ellipse((96, 70, 224, 198), fill=C(5, 6, 3))
d.ellipse((104, 78, 216, 190), fill=C(6, 7, 4))
for (cx, cy, r) in ((130, 110, 8), (190, 150, 11), (170, 96, 5), (140, 170, 6)):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=C(5, 6, 3))

# ---- searchlights
for (bx, ang, w) in ((40, -60, 6), (285, -118, 6), (250, -75, 5)):
    a1, a2 = math.radians(ang - w), math.radians(ang + w)
    L = 260
    d.polygon([(bx, 300), (bx + math.cos(a1) * L, 300 + math.sin(a1) * L),
               (bx + math.cos(a2) * L, 300 + math.sin(a2) * L)], fill=C(2, 2, 4))

# ---- ZHA'GORATH
kx, ky = 160, 168
# wings
for side in (-1, 1):
    pts = [(kx + side * 30, ky - 30), (kx + side * 70, ky - 92), (kx + side * 132, ky - 70),
           (kx + side * 122, ky - 36), (kx + side * 136, ky + 4), (kx + side * 104, ky + 2),
           (kx + side * 96, ky + 40), (kx + side * 40, ky + 30)]
    d.polygon(pts, fill=C(3, 0, 3), outline=C(5, 1, 4))
    for p in pts[1:7]:
        d.line(((kx + side * 34, ky - 22), p), fill=C(5, 1, 4), width=2)
# body / shoulders rising from the water
d.ellipse((kx - 70, ky + 10, kx + 70, ky + 140), fill=C(1, 2, 1), outline=C(0, 1, 0))
d.ellipse((kx - 50, ky + 16, kx + 10, ky + 70), fill=C(2, 3, 2))
# head
d.ellipse((kx - 48, ky - 62, kx + 48, ky + 40), fill=C(1, 2, 1), outline=C(0, 1, 0))
d.ellipse((kx - 38, ky - 56, kx + 12, ky - 6), fill=C(2, 3, 2))
d.ellipse((kx - 30, ky - 52, kx - 4, ky - 30), fill=C(3, 4, 2))
for k in range(-2, 3):
    d.arc((kx - 40 + k * 10, ky - 60, kx + 40 + k * 10, ky + 20), 200, 250, fill=C(1, 3, 2))
# horns
for i, hx in enumerate(range(kx - 36, kx + 40, 12)):
    top = ky - 84 if i in (3, 4) else ky - 76
    d.polygon([(hx - 5, ky - 52), (hx + 5, ky - 52), (hx + (2 if hx < kx else -2), top)], fill=C(4, 4, 2), outline=C(2, 2, 1))
    d.point((hx + (2 if hx < kx else -2), top + 1), fill=C(7, 7, 5))
# three eyes, glowing red
for (ex, ey) in ((kx - 22, ky - 22), (kx, ky - 32), (kx + 22, ky - 22)):
    d.ellipse((ex - 11, ey - 7, ex + 11, ey + 7), fill=C(2, 0, 0))
    d.ellipse((ex - 9, ey - 5, ex + 9, ey + 5), fill=C(7, 1, 1))
    d.ellipse((ex - 6, ey - 3, ex + 6, ey + 3), fill=C(7, 5, 1))
    d.rectangle((ex - 1, ey - 4, ex + 1, ey + 4), fill=C(0, 0, 0))
    d.point((ex - 5, ey - 3), fill=C(7, 7, 6))
# tentacle beard
for k, bx in enumerate(range(kx - 34, kx + 38, 7)):
    pts = []
    for s in range(14):
        t = s / 13
        pts.append((bx + math.sin(t * 4 + k * 0.8) * 7 * t, ky - 2 + t * 70))
    d.line(pts, fill=C(0, 1, 1), width=6)
    d.line(pts, fill=C(1, 3, 2), width=4)
    for (px, py) in pts[2::2]:
        d.point((px - 1, py), fill=C(4, 6, 4))
# two big tentacles reaching out to the city
for side in (-1, 1):
    pts = []
    for s in range(30):
        t = s / 29
        pts.append((kx + side * (30 + t * 120), ky + 50 + math.sin(t * 5) * 22 - t * 40))
    d.line(pts, fill=C(0, 1, 1), width=11)
    d.line(pts, fill=C(1, 3, 2), width=8)
    for (px, py) in pts[3::3]:
        d.ellipse((px - 2, py + 1, px + 2, py + 4), fill=C(4, 6, 4))
# fire breath stream toward the left skyline
for i in range(14):
    t = i / 13
    fx, fy = kx - 12 - t * 90, ky + 8 + t * 70
    r = 4 + t * 9
    d.ellipse((fx - r, fy - r, fx + r, fy + r), fill=C(7, 3, 0))
    d.ellipse((fx - r * 0.6, fy - r * 0.6, fx + r * 0.6, fy + r * 0.6), fill=C(7, 6, 1))

# ---- fighter jets with missile trails
for (jx, jy, dirn) in ((48, 74, 1), (262, 58, -1), (232, 110, -1)):
    d.polygon([(jx + dirn * 10, jy), (jx - dirn * 8, jy - 3), (jx - dirn * 8, jy + 3)], fill=C(5, 5, 6))
    d.polygon([(jx - dirn * 2, jy), (jx - dirn * 7, jy - 8), (jx - dirn * 5, jy)], fill=C(4, 4, 5))
    d.polygon([(jx - dirn * 2, jy), (jx - dirn * 7, jy + 8), (jx - dirn * 5, jy)], fill=C(4, 4, 5))
    d.line((jx - dirn * 9, jy, jx - dirn * 40, jy + 2), fill=C(4, 4, 5))
    mx = jx + dirn * 22
    d.line((jx + dirn * 10, jy + 1, mx, jy + 6), fill=C(6, 6, 6))
    d.ellipse((mx - 4, jy + 2, mx + 4, jy + 10), fill=C(7, 5, 1))

# ---- skyline + Empire State
sky = [(0, 26, 252), (26, 46, 236), (46, 70, 262), (70, 88, 246), (226, 246, 248),
       (246, 270, 230), (296, 320, 244), (88, 104, 268), (212, 226, 264)]
for (x0, x1, top) in sky:
    d.rectangle((x0, top, x1 - 1, 300), fill=C(0, 0, 1))
    for yy in range(top + 3, 298, 5):
        for xx in range(x0 + 2, x1 - 2, 4):
            if rnd.random() < 0.35:
                d.rectangle((xx, yy, xx + 1, yy + 1), fill=C(7, 6, 2))
# Empire State Building
ex = 283
d.rectangle((ex - 13, 210, ex + 13, 300), fill=C(1, 1, 2))
d.rectangle((ex - 9, 190, ex + 9, 210), fill=C(1, 1, 2))
d.rectangle((ex - 5, 174, ex + 5, 190), fill=C(1, 1, 2))
d.line((ex, 146, ex, 174), fill=C(3, 3, 4), width=2)
d.point((ex, 145), fill=C(7, 1, 1))
for yy in range(196, 298, 5):
    for xx in range(ex - 11, ex + 12, 4):
        if abs(xx - ex) < (8 if yy < 210 else 12) and rnd.random() < 0.5:
            d.point((xx, yy), fill=C(7, 6, 2))
# right big tentacle wraps the spire
d.arc((ex - 14, 176, ex + 14, 196), 0, 360, fill=C(1, 3, 2), width=5)

# ---- harbor water + Statue of Liberty
d.rectangle((0, 296, W, 312), fill=C(0, 1, 2))
for x in range(0, W, 12):
    d.line((x + 2, 302 + (x // 12) % 2 * 4, x + 8, 302 + (x // 12) % 2 * 4), fill=C(1, 3, 5))
lx = 26
cu, cu2 = C(2, 5, 4), C(1, 3, 3)
d.rectangle((lx - 14, 282, lx + 14, 300), fill=C(3, 3, 3), outline=C(4, 4, 4))
d.polygon([(lx - 8, 282), (lx + 8, 282), (lx + 4, 248), (lx - 4, 248)], fill=cu, outline=cu2)
d.ellipse((lx - 5, 238, lx + 5, 249), fill=cu, outline=cu2)
for sx in (-6, -3, 0, 3, 6):
    d.line((lx, 242, lx + sx, 233), fill=cu)
d.line((lx + 4, 250, lx + 9, 224), fill=cu, width=4)
d.rectangle((lx + 7, 218, lx + 12, 224), fill=C(5, 4, 1))
d.polygon([(lx + 6, 218), (lx + 13, 218), (lx + 9, 207)], fill=C(7, 3, 0))
d.polygon([(lx + 8, 218), (lx + 11, 218), (lx + 9, 211)], fill=C(7, 7, 2))

# ---- marquee title
d.rectangle((0, 0, W, 44), fill=C(0, 0, 0))
glyph_text("KAIJU SIEGE", (W - text_w("KAIJU SIEGE", 4)) // 2, 6, 4,
           lambda r: [C(7, 7, 2), C(7, 7, 1), C(7, 6, 0), C(7, 5, 0), C(7, 4, 0), C(7, 2, 0), C(6, 1, 0)][r],
           outline=C(2, 0, 0), shadow=C(4, 0, 0))
d.rectangle((0, 40, W, 42), fill=C(6, 5, 2))
# ribbon
d.polygon([(60, 48), (260, 48), (252, 58), (260, 68), (60, 68), (68, 58)], fill=C(0, 3, 4), outline=C(1, 6, 7))
glyph_text("MANHATTAN", (W - text_w("MANHATTAN", 2)) // 2, 51, 2, lambda r: C(7, 7, 7), shadow=C(0, 1, 2))
# subtitle on the moon's lower edge
sub = "ZHA'GORATH - THE DROWNED KING"
glyph_text(sub, (W - text_w(sub, 1)) // 2, 74, 1, lambda r: C(5, 7, 2), shadow=C(0, 0, 0))

# ---- score panel
d.rectangle((0, 312, W, H), fill=C(0, 0, 0))
d.rectangle((0, 312, W, 314), fill=C(6, 5, 2))
def window(x0, y0, x1, y1):
    d.rectangle((x0, y0, x1, y1), fill=C(1, 0, 0), outline=C(4, 4, 4))
window(10, 320, 158, 340)
glyph_text("00000000", 18, 326, 2 if False else 1, lambda r: C(7, 3, 0))
glyph_text("PLAYER 1", 18, 344, 1, lambda r: C(5, 5, 5))
# big score digits
d.rectangle((10, 320, 158, 340), fill=C(1, 0, 0), outline=C(4, 4, 4))
glyph_text("00000000", 20, 324, 2, lambda r: C(7, 3, 0))
window(166, 320, 226, 340)
glyph_text("BALL", 176, 323, 1, lambda r: C(5, 5, 5))
glyph_text("1", 202, 330, 1, lambda r: C(7, 3, 0))
window(234, 320, 310, 330)
glyph_text("GAME OVER", 240, 322, 1, lambda r: C(7, 1, 1))
window(234, 332, 310, 342)
glyph_text("TILT", 260, 334, 1, lambda r: C(3, 0, 0))
glyph_text("A XENOCIDE21 GAME", 166, 348, 1, lambda r: C(6, 5, 2))

# ---- frame
d.rectangle((0, 0, W - 1, H - 1), outline=C(6, 5, 2))
d.rectangle((1, 1, W - 2, H - 2), outline=C(3, 2, 1))

out = os.path.join(os.path.dirname(__file__), '..', 'docs', 'backglass.png')
img.resize((W * S, H * S), Image.NEAREST).save(out)
print('wrote', out)
