"""Bonus rooms for Kaiju Siege: 256x208 single-screen mini tables."""
import math, random
import numpy as np
from PIL import Image, ImageDraw

RW, RH = 256, 208
RLP = (93, 186); RRP = (163, 186)

def rmirror(pts):
    return [(256 - x, y) for (x, y) in pts]

R_LLOW = [(8, 148), (89, 182), (92, 190), (84, 208), (8, 208)]
R_RLOW = rmirror(R_LLOW)
SWITCHES = [(56, 8), (120, 8), (184, 8)]          # 16x6 targets on the top wall
SUB_BUMPERS = [(72, 132), (184, 132)]
ROOF_FACE = (20, -70, 236, 78)
ROOF_EYES = [(72, 92), (128, 84), (184, 92)]
ROOF_TENT = [100, 156]
ROOF_BUMPERS = [(34, 120), (222, 120)]
ALTAR = (100, 18, 155, 52)
SHRINE_PILLARS = [(56, 96), (200, 96)]

def room_frame(d, MAT_WALL):
    d.rectangle((0, 0, 7, RH - 1), fill=MAT_WALL)
    d.rectangle((248, 0, 255, RH - 1), fill=MAT_WALL)
    d.rectangle((0, 0, 255, 7), fill=MAT_WALL)
    d.polygon(R_LLOW, fill=MAT_WALL); d.polygon(R_RLOW, fill=MAT_WALL)

def round_corners(a, MAT_WALL, r=32):
    yy, xx = np.mgrid[0:RH, 0:RW]
    a[(xx < r + 8) & (yy < r + 8) & ((xx - r - 8) ** 2 + (yy - r - 8) ** 2 > r ** 2)] = MAT_WALL
    a[(xx > 247 - r) & (yy < r + 8) & ((xx - 247 + r) ** 2 + (yy - r - 8) ** 2 > r ** 2)] = MAT_WALL
    return a

def build_room_mat(kind, M):
    img = Image.new('L', (RW, RH), 0)
    d = ImageDraw.Draw(img)
    room_frame(d, M['WALL'])
    if kind == 1:
        for (x, y) in SWITCHES:
            d.rectangle((x, y, x + 15, y + 5), fill=M['EMPIRE'])
        for (x, y) in SUB_BUMPERS:
            d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=M['BUMP'])
    elif kind == 2:
        d.ellipse(ROOF_FACE, fill=M['BOSS'])
        for (x, y) in ROOF_BUMPERS:
            d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=M['BUMP'])
    elif kind == 3:
        d.rectangle(ALTAR, fill=M['BOSS'])
        for (x, y) in SHRINE_PILLARS:
            d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=M['BUMP'])
    a = round_corners(np.array(img), M['WALL'])
    return a

def draw_room(kind, mat, H, variant=0):
    """H: helper namespace from gen_assets (C, text, window_grid, color_walls)."""
    C, text = H.C, H.text
    img = Image.new('RGB', (RW, RH), (0, 0, 0))
    d = ImageDraw.Draw(img)
    if kind == 1:
        # brick tunnel
        d.rectangle((0, 0, RW - 1, RH - 1), fill=C(1, 1, 1))
        for y in range(8, RH, 8):
            d.line((0, y, RW - 1, y), fill=C(2, 1, 1))
            off = 8 if (y // 8) % 2 else 0
            for x in range(off, RW, 16):
                d.line((x, y, x, y + 7), fill=C(2, 1, 1))
        # track bed
        d.rectangle((8, 80, 247, 104), fill=C(1, 1, 0))
        for x in range(8, 248, 8):
            d.rectangle((x + 1, 82, x + 4, 102), fill=C(3, 2, 1))
        d.line((8, 86, 247, 86), fill=C(5, 5, 6)); d.line((8, 98, 247, 98), fill=C(5, 5, 6))
        d.line((8, 103, 247, 103), fill=C(6, 5, 1))
        # signals
        for (x, col) in ((20, C(7, 1, 1)), (236, C(2, 7, 2))):
            d.rectangle((x - 4, 60, x + 4, 76), fill=C(0, 0, 0), outline=C(3, 3, 3))
            d.ellipse((x - 2, 63, x + 2, 67), fill=col)
        text(d, "DERAIL THE TRAIN!", 128 - 51, 40, C(7, 6, 1), shadow=C(2, 1, 0))
        text(d, "EXPRESS", 128 - 21, 116, C(2, 7, 2))
    elif kind == 2:
        # night sky + far skyline
        d.rectangle((0, 0, RW - 1, RH - 1), fill=C(0, 0, 2))
        for (x0, x1, top) in [(8, 30, 112), (30, 52, 100), (204, 226, 104), (226, 248, 116)]:
            H.window_grid(d, x0, top, x1 - 1, 150, C(7, 6, 2), C(1, 1, 2), C(0, 0, 1), seed=x0)
        # the face
        d.ellipse(ROOF_FACE, fill=C(1, 2, 1), outline=C(0, 1, 0))
        d.ellipse((40, -60, 170, 40), fill=C(2, 3, 2))
        d.ellipse((60, -50, 140, 14), fill=C(3, 4, 2))
        for k in range(-3, 4):
            d.arc((40 + k * 14, -60, 216 + k * 14, 70), 200, 250, fill=C(1, 3, 2))
        for hx in range(40, 220, 20):
            d.polygon([(hx - 5, 8), (hx + 5, 8), (hx, -6)], fill=C(4, 4, 2))
        for (ex, ey) in ROOF_EYES:
            d.ellipse((ex - 16, ey - 12, ex + 16, ey + 12), fill=C(0, 0, 0))
        # beard behind eyes
        for k, bx in enumerate(range(84, 176, 8)):
            pts = [(bx + math.sin(s / 2 + k) * 3, 64 + s * 4) for s in range(10)]
            d.line(pts, fill=C(1, 3, 2), width=3)
        # rooftop floor
        d.rectangle((8, 140, 247, RH - 1), fill=C(2, 2, 2))
        rnd = random.Random(3)
        for y in range(144, RH, 4):
            for x in range(10, 246, 8):
                d.point((x + (y // 4) % 4, y), fill=C(3, 3, 3))
        d.line((8, 140, 247, 140), fill=C(4, 4, 4))
        # water tower + AC unit
        tx, ty = ROOF_BUMPERS[0]
        d.ellipse((tx - 10, ty - 10, tx + 10, ty + 10), fill=C(4, 2, 1), outline=C(6, 4, 2))
        for k in range(-6, 7, 4):
            d.line((tx + k, ty - 9, tx + k, ty + 9), fill=C(3, 1, 0))
        ax, ay = ROOF_BUMPERS[1]
        d.ellipse((ax - 10, ay - 10, ax + 10, ay + 10), fill=C(4, 4, 5), outline=C(6, 6, 7))
        d.ellipse((ax - 6, ay - 6, ax + 6, ay + 6), fill=C(1, 1, 2))
        d.line((ax - 5, ay, ax + 5, ay), fill=C(5, 5, 6)); d.line((ax, ay - 5, ax, ay + 5), fill=C(5, 5, 6))
        text(d, "SHOOT HIS EYES!", 128 - 45, 150, C(7, 2, 1), shadow=C(1, 0, 0))
    elif kind == 3:
        # flooded subway station: white tile walls under green water
        d.rectangle((0, 0, RW - 1, RH - 1), fill=C(0, 2, 3))
        for y in range(0, RH, 4):
            for x in range(0, RW, 8):
                off = 4 if (y // 4) % 2 else 0
                d.line((x + off, y, x + off + 6, y), fill=C(1, 3, 3))
        for y in range(10, RH, 16):
            for x in range(0, RW, 32):
                off = 16 if (y // 16) % 2 else 0
                d.line((x + off + 3, y, x + off + 10, y), fill=C(2, 5, 5))
        # station name band
        d.rectangle((8, 160, 247, 172), fill=C(0, 3, 1))
        text(d, "SHRINE ST", 128 - 27, 163, C(6, 6, 6))
        # altar
        x0, y0, x1, y1 = ALTAR
        if variant < 2:
            d.rectangle((x0, y0, x1, y1), fill=C(3, 3, 2), outline=C(5, 5, 4))
            d.rectangle((x0 + 4, y0 + 22, x1 - 4, y1 - 2), fill=C(2, 2, 1))
            for k in range(3):
                d.line((x0 + 6 + k * 16, y0 + 24, x0 + 14 + k * 16, y0 + 30), fill=C(1, 4, 2))
            # idol
            glow = C(5, 7, 3) if variant == 0 else C(3, 5, 2)
            d.ellipse((120, y0 + 2, 135, y0 + 16), fill=C(1, 4, 2), outline=glow)
            for k in range(4):
                d.line((122 + k * 4, y0 + 14, 121 + k * 4, y0 + 21), fill=C(1, 4, 2), width=2)
            d.point((125, y0 + 7), fill=glow); d.point((130, y0 + 7), fill=glow)
            if variant == 1:
                d.line((x0 + 8, y0 + 2, x0 + 20, y0 + 20), fill=C(0, 0, 0), width=2)
                d.line((x1 - 6, y0 + 4, x1 - 18, y0 + 22), fill=C(0, 0, 0), width=2)
                d.line((x0 + 30, y1 - 2, x0 + 40, y0 + 18), fill=C(0, 0, 0))
        else:
            for k in range(14):
                rx = x0 + (k * 37) % 52; ry = y0 + 8 + (k * 23) % 28
                d.polygon([(rx, ry), (rx + 6, ry + 1), (rx + 4, ry + 5)], fill=C(3, 3, 2), outline=C(1, 1, 1))
        # candles
        for cx in (84, 172):
            d.rectangle((cx - 2, 30, cx + 2, 44), fill=C(6, 6, 5))
            d.polygon([(cx - 2, 30), (cx + 2, 30), (cx, 24)], fill=C(7, 5, 0))
        # pillars
        for (px, py) in SHRINE_PILLARS:
            d.ellipse((px - 11, py - 11, px + 11, py + 11), fill=C(5, 5, 5), outline=C(7, 7, 7))
            d.ellipse((px - 7, py - 7, px + 7, py + 7), fill=C(1, 4, 2))
            d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=C(3, 6, 3))
    H.color_walls(img, mat)
    d = ImageDraw.Draw(img)
    if kind == 1:
        for i, (x, y) in enumerate(SWITCHES):
            lit = variant == 1
            d.rectangle((x, y, x + 15, y + 5), fill=C(2, 7, 2) if lit else C(7, 1, 1), outline=C(7, 7, 7))
            d.rectangle((x + 4, y + 1, x + 11, y + 3), fill=C(6, 7, 6) if lit else C(4, 0, 0))
        for (x, y) in SUB_BUMPERS:
            d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=C(2, 7, 2), outline=C(6, 7, 6))
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=C(6, 7, 6))
    return img
