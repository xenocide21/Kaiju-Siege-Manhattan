#!/usr/bin/env python3
"""Kaiju Siege: Manhattan -- asset generator.
Builds table art, collision grid, BG tiles/palettes/BAT, sprites and gen.h for HuCC.
All colors are 3-bit-per-channel (0-7) like the PC Engine VCE.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, os.path.dirname(__file__))
from font import GLYPHS, CHARS

OUT = os.path.join(os.path.dirname(__file__), '..', 'src', 'data')
PREV = os.path.join(os.path.dirname(__file__), '..', 'preview')
os.makedirs(OUT, exist_ok=True); os.makedirs(PREV, exist_ok=True)

W, H = 256, 512
R = 4  # ball radius in px

def C(r, g, b):
    return (r * 36, g * 36, b * 36)

# ---------------------------------------------------------------- geometry
LP = (84, 467); RP = (150, 467)           # flipper pivots
FL_LEN = 27
BUMPERS = [(86, 200), (146, 200), (116, 240)]
BUMP_R = 11
TARGETS = [(88, 320), (112, 320), (136, 320)]   # 16x8 drop targets (x,y top-left)
SUBWAY = (54, 292)
KAIJU_BOX = (82, 30, 150, 96)
MAT_WALL, MAT_SLING, MAT_BUMP, MAT_BOSS, MAT_EMPIRE = 1, 2, 3, 4, 5

def mirror(pts):
    return [(234 - x, y) for (x, y) in pts]

LSLING = [(36, 382), (36, 422), (66, 440)]
RSLING = mirror(LSLING)
LLOW = [(23, 436), (80, 464), (83, 471), (70, 512), (23, 512)]
RLOW = mirror(LLOW)
LWING = [(88, 43), (66, 48), (50, 58), (50, 68), (58, 84), (66, 96), (88, 86)]
RWING = mirror(LWING)
SEPS = [(20, 396, 23, 436), (211, 396, 214, 436)]
EMPIRE_BLOCK = (204, 196, 225, 286)
EMPIRE_FACE = (199, 214, 203, 266)

def build_mat():
    img = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 7, H - 1), fill=MAT_WALL)
    d.rectangle((248, 0, 255, H - 1), fill=MAT_WALL)
    d.rectangle((0, 0, 255, 7), fill=MAT_WALL)
    a = np.array(img)
    yy, xx = np.mgrid[0:H, 0:W]
    a[(xx < 56) & (yy < 56) & ((xx - 56) ** 2 + (yy - 56) ** 2 > 48 ** 2)] = MAT_WALL
    a[(xx > 200) & (yy < 56) & ((xx - 200) ** 2 + (yy - 56) ** 2 > 48 ** 2)] = MAT_WALL
    img = Image.fromarray(a); d = ImageDraw.Draw(img)
    # plunger lane
    d.rectangle((226, 140, 231, H - 1), fill=MAT_WALL)
    d.ellipse((226, 137, 231, 143), fill=MAT_WALL)
    d.rectangle((232, 500, 247, H - 1), fill=MAT_WALL)
    for s in SEPS:
        d.rectangle(s, fill=MAT_WALL)
        d.ellipse((s[0], s[1] - 2, s[2], s[1] + 2), fill=MAT_WALL)
    d.polygon(LLOW, fill=MAT_WALL); d.polygon(RLOW, fill=MAT_WALL)
    for tri in (LSLING, RSLING):
        d.polygon(tri, fill=MAT_WALL)
        d.line([tri[0], tri[2]], fill=MAT_SLING, width=3)
    d.polygon(LWING, fill=MAT_WALL); d.polygon(RWING, fill=MAT_WALL)
    d.ellipse(KAIJU_BOX, fill=MAT_BOSS)
    for (bx, by) in BUMPERS:
        d.ellipse((bx - BUMP_R, by - BUMP_R, bx + BUMP_R, by + BUMP_R), fill=MAT_BUMP)
    d.rectangle(EMPIRE_BLOCK, fill=MAT_WALL)
    d.rectangle(EMPIRE_FACE, fill=MAT_EMPIRE)
    return np.array(img)

def build_collision(mat):
    solid = mat > 0
    dist_free, ind_free = ndimage.distance_transform_edt(~solid, return_indices=True)  # free px -> nearest solid
    dist_sol, ind_sol = ndimage.distance_transform_edt(solid, return_indices=True)     # solid px -> nearest free
    GH, GW = mat.shape[0] // 2, mat.shape[1] // 2
    grid = np.zeros((GH, GW), np.uint8)
    for j in range(GH):
        for i in range(GW):
            px, py = 2 * i + 1, 2 * j + 1
            if solid[py, px]:
                ny, nx = ind_sol[0][py, px], ind_sol[1][py, px]
                vx, vy = nx - px, ny - py
                m = mat[py, px]
            elif dist_free[py, px] < R:
                sy, sx = ind_free[0][py, px], ind_free[1][py, px]
                vx, vy = px - sx, py - sy
                m = mat[sy, sx]
            else:
                continue
            if vx == 0 and vy == 0:
                vy = -1
            k = int(round(math.atan2(vy, vx) / (2 * math.pi) * 32)) % 32
            grid[j, i] = (m << 5) | k
    return grid

# ---------------------------------------------------------------- drawing helpers
def text(d, s, x, y, col, scale=1, shadow=None):
    cx = x
    for ch in s:
        g = GLYPHS.get(ch, GLYPHS[' '])
        for ry, row in enumerate(g):
            for rx, bit in enumerate(row):
                if bit == '1':
                    if shadow:
                        d.rectangle((cx + rx * scale + scale, y + ry * scale + scale,
                                     cx + rx * scale + 2 * scale - 1, y + ry * scale + 2 * scale - 1), fill=shadow)
        for ry, row in enumerate(g):
            for rx, bit in enumerate(row):
                if bit == '1':
                    d.rectangle((cx + rx * scale, y + ry * scale,
                                 cx + rx * scale + scale - 1, y + ry * scale + scale - 1), fill=col)
        cx += 6 * scale

def window_grid(d, x0, y0, x1, y1, lit, dim, wall, seed=0):
    d.rectangle((x0, y0, x1, y1), fill=wall)
    for yy in range(y0 + 2, y1 - 2, 4):
        for xx in range(x0 + 2, x1 - 1, 4):
            k = ((xx // 4) * 7 + (yy // 4) * 3 + seed) % 5
            d.rectangle((xx, yy, xx + 1, yy + 1), fill=lit if k == 0 else dim)

# ---------------------------------------------------------------- table art
def draw_table(mat, variant=False):
    img = Image.new('RGB', (W, H), C(0, 0, 0))
    d = ImageDraw.Draw(img)
    # --- Zone 3: Hudson + Central Park (y 0-160)
    d.rectangle((0, 0, W - 1, 112), fill=C(0, 1, 2))
    for y in range(12, 112, 8):
        for x in range(0, W, 16):
            off = 8 if (y // 8) % 2 else 0
            d.line((x + off + 2, y + 3, x + off + 7, y + 3), fill=C(0, 2, 4))
    d.rectangle((0, 113, W - 1, 160), fill=C(0, 2, 1))
    d.rectangle((0, 112, W - 1, 113), fill=C(1, 3, 4))  # shoreline
    for y in range(120, 160, 8):
        for x in range(8, 226, 16):
            off = 8 if (y // 8) % 2 else 0
            d.point((x + off + 3, y + 4), fill=C(0, 3, 1))
    for (tx, ty) in [(20, 134), (44, 146), (192, 134), (170, 148), (210, 120), (28, 120)]:
        d.ellipse((tx - 7, ty - 6, tx + 7, ty + 6), fill=C(0, 3, 1))
        d.ellipse((tx - 5, ty - 5, tx + 3, ty + 2), fill=C(1, 4, 1))
        d.point((tx - 2, ty - 3), fill=C(2, 5, 2))
    d.line((60, 160, 116, 118, 172, 160), fill=C(3, 3, 2), width=3)  # park path
    text(d, "CENTRAL PARK", 82, 146, C(2, 5, 2))
    # --- Zone 2: Midtown (y 160-312)
    d.rectangle((0, 161, W - 1, 312), fill=C(1, 0, 2))
    window_grid(d, 8, 166, 44, 284, C(7, 5, 1), C(2, 1, 3), C(1, 1, 3), seed=1)
    window_grid(d, 176, 166, 198, 284, C(7, 5, 1), C(2, 1, 3), C(1, 1, 3), seed=2)
    # Times Square billboard frames
    for (x0, y0, x1, y1, col) in [(52, 170, 84, 186, C(7, 1, 6)), (148, 170, 172, 186, C(1, 6, 7)),
                                  (52, 252, 80, 268, C(7, 4, 0)), (152, 252, 172, 268, C(7, 7, 1))]:
        d.rectangle((x0, y0, x1, y1), fill=C(0, 0, 1), outline=col)
        for xx in range(x0 + 3, x1 - 2, 4):
            d.line((xx, y0 + 4, xx, y1 - 4), fill=col)
    text(d, "TIMES SQ", 92, 168, C(7, 1, 6), shadow=C(2, 0, 2))
    # tank avenue
    d.rectangle((8, 288, 225, 304), fill=C(1, 1, 1))
    for x in range(12, 224, 16):
        d.line((x, 296, x + 7, 296), fill=C(5, 5, 5))
    # subway entrance
    sx, sy = SUBWAY
    d.rectangle((sx - 9, sy - 7, sx + 9, sy + 7), fill=C(0, 2, 1))
    d.ellipse((sx - 7, sy - 6, sx + 7, sy + 6), fill=C(0, 0, 0))
    for k in range(4):
        d.line((sx - 5 + k, sy - 3 + k * 2, sx + 5 - k, sy - 3 + k * 2), fill=C(2, 2, 2))
    d.ellipse((sx - 12, sy - 10, sx - 8, sy - 6), fill=C(2, 7, 2))
    d.ellipse((sx + 8, sy - 10, sx + 12, sy - 6), fill=C(2, 7, 2))
    text(d, "SUBWAY", sx - 18, sy + 9, C(2, 7, 2))
    # Empire State Building
    ex0, ey0, ex1, ey1 = EMPIRE_BLOCK
    d.rectangle((ex0, ey0, ex1, ey1), fill=C(3, 3, 4))
    d.rectangle((ex0 + 3, ey0 - 14, ex1 - 3, ey0), fill=C(3, 3, 4))
    d.rectangle((ex0 + 7, ey0 - 26, ex1 - 7, ey0 - 14), fill=C(3, 3, 4))
    d.line((214, ey0 - 44, 214, ey0 - 26), fill=C(5, 5, 6), width=2)
    d.point((214, ey0 - 45), fill=C(7, 1, 1))
    for yy in range(ey0 + 4, 236, 4):
        for xx in range(ex0 + 4, ex1 - 2, 4):
            d.point((xx, yy), fill=C(6, 5, 2))
    for lvl in range(5):
        y = 272 - lvl * 8
        col = C(7, 7, 2) if variant else C(1, 1, 2)
        d.rectangle((209, y + 1, 222, y + 6), fill=C(2, 2, 3))
        for xx in range(210, 222, 3):
            d.rectangle((xx, y + 2, xx + 1, y + 5), fill=col)
    ef = EMPIRE_FACE
    d.rectangle(ef, fill=C(7, 1, 1)); d.line((ef[0], ef[1], ef[0], ef[3]), fill=C(7, 7, 7))
    # --- Zone 1: Lower Manhattan (y 312-512)
    d.rectangle((0, 313, W - 1, H - 1), fill=C(0, 0, 2))
    for (x0, x1, top, seed) in [(8, 34, 330, 3), (180, 198, 336, 4), (8, 30, 360, 5), (196, 225, 340, 6)]:
        window_grid(d, x0, top, x1, 380, C(6, 6, 3), C(1, 1, 3), C(1, 1, 2), seed)
    text(d, "WALL STREET", 86, 310, C(7, 6, 1), shadow=C(3, 2, 0))
    d.rectangle((24, 346, 210, 366), fill=C(1, 1, 1))
    for x in range(28, 208, 16):
        d.line((x, 356, x + 7, 356), fill=C(7, 6, 0))
    for i, (tx, ty) in enumerate(TARGETS):
        if variant:
            d.rectangle((tx + 1, ty + 5, tx + 14, ty + 7), fill=C(1, 1, 1))
        else:
            d.rectangle((tx + 1, ty + 1, tx + 14, ty + 7), fill=C(5, 4, 0))
            d.rectangle((tx + 2, ty + 1, tx + 13, ty + 3), fill=C(7, 6, 1))
            d.line((tx + 7, ty + 2, tx + 8, ty + 6), fill=C(3, 2, 0))
    # harbor at drain
    d.rectangle((0, 488, W - 1, H - 1), fill=C(0, 1, 2))
    for x in range(0, W, 16):
        d.line((x + 2, 498, x + 8, 498), fill=C(0, 2, 4))
    # plunger lane
    d.rectangle((232, 140, 247, 499), fill=C(0, 0, 1))
    for y in range(160, 480, 24):
        d.line((236, y + 6, 239, y, 243, y + 6), fill=C(2, 1, 0))
    # --- walls from material map
    color_walls(img, mat)
    d = ImageDraw.Draw(img)
    draw_table_props(d, variant)
    return img

def color_walls(img, mat):
    solid = mat > 0
    edge = solid & ~ndimage.binary_erosion(solid)
    edge2 = solid & ~ndimage.binary_erosion(solid, iterations=2) & ~edge
    a = np.array(img)
    wallm = (mat == MAT_WALL)
    a[wallm] = C(1, 1, 2)
    a[wallm & edge2] = C(3, 3, 4)
    a[wallm & edge] = C(5, 5, 6)
    sl = mat == MAT_SLING
    a[sl] = C(7, 1, 1)
    a[sl & edge] = C(7, 7, 7)
    img.paste(Image.fromarray(a))

def draw_table_props(d, variant):
    ef = EMPIRE_FACE
    # slings: inner glow
    for tri in (LSLING, RSLING):
        cx = sum(p[0] for p in tri) // 3; cy = sum(p[1] for p in tri) // 3
        d.polygon([((p[0] * 2 + cx) // 3, (p[1] * 2 + cy) // 3) for p in tri], fill=C(3, 0, 1))
    # bumpers
    for (bx, by) in BUMPERS:
        ring = C(7, 6, 7) if variant else C(7, 1, 6)
        inner = C(7, 2, 6) if variant else C(3, 0, 3)
        d.ellipse((bx - BUMP_R, by - BUMP_R, bx + BUMP_R, by + BUMP_R), fill=ring)
        d.ellipse((bx - BUMP_R + 3, by - BUMP_R + 3, bx + BUMP_R - 3, by + BUMP_R - 3), fill=inner)
        d.line((bx - 4, by, bx + 4, by), fill=C(7, 7, 7)); d.line((bx, by - 4, bx, by + 4), fill=C(7, 7, 7))
        d.point((bx - 3, by - 3), fill=C(7, 7, 7)); d.point((bx + 3, by + 3), fill=C(7, 7, 7))
        d.point((bx + 3, by - 3), fill=C(7, 7, 7)); d.point((bx - 3, by + 3), fill=C(7, 7, 7))
    draw_kaiju(d)
    draw_liberty(d, variant)
    draw_bridge(d)
    # empire face re-draw over generic wall coloring
    d.rectangle(ef, fill=C(7, 1, 1)); d.line((ef[0], ef[1], ef[0], ef[3]), fill=C(7, 7, 7))

def draw_kaiju(d):
    # wings
    for wing in (LWING, RWING):
        d.polygon(wing, fill=C(2, 0, 2), outline=C(4, 1, 4))
        root = wing[0]
        for p in wing[1:5]:
            d.line((root, p), fill=C(4, 1, 4))
    # water ripples at base
    d.ellipse((66, 88, 166, 110), outline=C(1, 3, 5))
    d.ellipse((76, 92, 156, 106), outline=C(0, 2, 4))
    # head
    x0, y0, x1, y1 = KAIJU_BOX
    d.ellipse((x0, y0, x1, y1), fill=C(1, 2, 1), outline=C(0, 1, 0))
    d.ellipse((x0 + 8, y0 + 3, x1 - 20, y0 + 34), fill=C(2, 3, 2))
    d.ellipse((x0 + 14, y0 + 5, x1 - 34, y0 + 18), fill=C(3, 4, 2))
    for k in range(-2, 3):
        d.arc((x0 + 10 + k * 6, y0 + 2, x1 - 10 + k * 6, y1 - 20), 200, 250, fill=C(1, 3, 2))
    # horn crown
    for hx in (92, 102, 112, 122, 132, 142):
        top = 22 if hx in (112, 122) else 25
        d.polygon([(hx - 3, 36), (hx + 3, 36), (hx + (1 if hx < 117 else -1), top)], fill=C(4, 4, 2), outline=C(2, 2, 1))
        d.point((hx + (1 if hx < 117 else -1), top + 1), fill=C(6, 6, 4))
    # eye sockets (closed)
    for (ex, ey) in ((100, 54), (116, 47), (132, 54)):
        d.ellipse((ex - 6, ey - 4, ex + 6, ey + 4), fill=C(0, 0, 0))
        d.line((ex - 5, ey, ex + 5, ey), fill=C(2, 4, 2))
    # tentacle beard
    d.ellipse((94, 66, 138, 92), fill=C(0, 1, 0))
    import random
    rnd = random.Random(7)
    for k, bx in enumerate(range(92, 144, 6)):
        pts = []
        for s in range(9):
            t = s / 8
            px = bx + math.sin(t * 3 + k) * 4
            py = 66 + t * 34
            pts.append((px, py))
        d.line(pts, fill=C(1, 3, 2), width=3)
        for (px, py) in pts[2::2]:
            d.point((px, py), fill=C(3, 5, 3))

def draw_liberty(d, lit):
    # statue on the lower-left apron
    base = C(3, 3, 3)
    d.rectangle((30, 494, 62, 511), fill=base, outline=C(5, 5, 5))
    d.rectangle((34, 488, 58, 494), fill=C(4, 4, 4))
    cu, cu2 = C(2, 5, 4), C(1, 3, 3)
    d.polygon([(38, 488), (54, 488), (50, 466), (42, 466)], fill=cu, outline=cu2)
    d.ellipse((42, 459, 50, 467), fill=cu, outline=cu2)
    for sx in (41, 44, 46, 48, 51):
        d.line((46, 462, sx, 456), fill=cu)
    d.line((43, 468, 38, 458), fill=cu, width=3)  # raised arm
    d.rectangle((36, 455, 39, 458), fill=C(5, 4, 1))
    flame = C(7, 6, 1) if lit else C(2, 2, 2)
    flame2 = C(7, 3, 0) if lit else C(1, 1, 1)
    d.polygon([(35, 455), (40, 455), (38, 449)], fill=flame2)
    d.polygon([(36, 455), (39, 455), (38, 451)], fill=flame)
    d.rectangle((50, 470, 54, 476), fill=cu2)  # tablet

def draw_bridge(d):
    st, dk = C(4, 3, 2), C(2, 1, 1)
    d.rectangle((174, 470, 202, 511), fill=st, outline=C(5, 4, 3))
    d.rectangle((179, 480, 186, 498), fill=dk); d.ellipse((179, 476, 186, 484), fill=dk)
    d.rectangle((190, 480, 197, 498), fill=dk); d.ellipse((190, 476, 197, 484), fill=dk)
    for k in range(5):
        d.line((174, 474 + k * 3, 160 + k * 2, 500), fill=C(5, 5, 5))
        d.line((202, 474 + k * 3, 211 - k, 492), fill=C(5, 5, 5))
    text(d, "BKLYN", 174, 502, C(6, 6, 6))

# ---------------------------------------------------------------- title screen
def draw_title():
    img = Image.new('RGB', (256, 224), C(0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, col in enumerate([C(0, 0, 1), C(0, 0, 2), C(1, 0, 2), C(1, 0, 3)]):
        d.rectangle((0, 96 + i * 16, 255, 111 + i * 16), fill=col)
    d.rectangle((0, 160, 255, 223), fill=C(1, 0, 3))
    # kaiju silhouette rising behind skyline
    d.polygon([(128, 104), (70, 70), (56, 100), (64, 160)], fill=C(1, 0, 1))
    d.polygon([(128, 104), (186, 70), (200, 100), (192, 160)], fill=C(1, 0, 1))
    d.ellipse((92, 96, 164, 170), fill=C(0, 1, 0))
    for (ex, ey) in ((110, 122), (128, 114), (146, 122)):
        d.ellipse((ex - 6, ey - 3, ex + 6, ey + 3), fill=C(6, 7, 2))
        d.line((ex, ey - 2, ex, ey + 2), fill=C(0, 0, 0))
    for k, bx in enumerate(range(104, 156, 6)):
        pts = [(bx + math.sin(s / 3 + k) * 3, 136 + s * 4) for s in range(8)]
        d.line(pts, fill=C(1, 3, 2), width=3)
    for hx in (104, 116, 128, 140, 152):
        d.polygon([(hx - 3, 102), (hx + 3, 102), (hx, 90)], fill=C(3, 3, 2))
    # skyline
    sky = [(0, 22, 168), (22, 40, 150), (40, 58, 176), (60, 76, 160), (176, 194, 156),
           (194, 214, 172), (214, 236, 146), (236, 256, 166), (78, 92, 182), (164, 178, 180)]
    for (x0, x1, top) in sky:
        window_grid(d, x0, top, x1 - 1, 223, C(7, 6, 2), C(1, 1, 2), C(0, 0, 1), seed=x0)
    d.rectangle((38, 136, 44, 150), fill=C(0, 0, 1)); d.line((41, 124, 41, 136), fill=C(2, 2, 3))
    d.rectangle((0, 210, 255, 223), fill=C(0, 0, 0))
    # logo
    text(d, "KAIJU", 53, 10, C(7, 6, 0), scale=5, shadow=C(5, 1, 0))
    text(d, "SIEGE", 53, 50, C(7, 2, 0), scale=5, shadow=C(3, 0, 0))
    text(d, "MANHATTAN", 74, 88, C(1, 6, 7), scale=2, shadow=C(0, 1, 3))
    return img

# ---------------------------------------------------------------- tile conversion
def q(img):
    a = np.array(img.convert('RGB')).astype(int)
    return np.clip((a + 18) // 36, 0, 7)

class TilePool:
    def __init__(self, reserved_pals):
        self.tiles = []        # list of 64-tuples of indices
        self.index = {}
        self.pals = [[] for _ in range(16)]
        self.free_pals = [p for p in range(16) if p not in reserved_pals]
    def add_tile(self, idx_tuple):
        if idx_tuple in self.index:
            return self.index[idx_tuple]
        self.index[idx_tuple] = len(self.tiles)
        self.tiles.append(idx_tuple)
        return self.index[idx_tuple]
    def pal_for(self, colors):
        best, bestadd = None, 99
        for p in self.free_pals:
            pal = self.pals[p]
            add = len([c for c in colors if c not in pal])
            if len(pal) + add <= 15 and add < bestadd:
                best, bestadd = p, add
                if add == 0:
                    break
        if best is None:
            raise RuntimeError('out of palettes for colors %r' % (colors,))
        for c in colors:
            if c not in self.pals[best]:
                self.pals[best].append(c)
        return best
    def convert(self, qa, tx0, ty0, tw, th):
        """Convert tile rect of quantized array -> BAT entries (2D list)."""
        rows = []
        cells = []
        for ty in range(th):
            for tx in range(tw):
                blk = qa[ty * 8:(ty + 1) * 8, tx * 8:(tx + 1) * 8]
                cols = sorted(set(tuple(p) for p in blk.reshape(-1, 3)) - {(0, 0, 0)}, key=lambda c: -int(((blk == c).all(axis=2)).sum()))
                cells.append((tx, ty, blk, cols))
        # assign palettes: biggest color sets first
        assign = {}
        for (tx, ty, blk, cols) in sorted(cells, key=lambda c: -len(c[3])):
            assign[(tx, ty)] = self.pal_for(cols) if cols else 0
        bat = [[0] * tw for _ in range(th)]
        for (tx, ty, blk, cols) in cells:
            p = assign[(tx, ty)]
            pal = self.pals[p]
            idx = tuple(0 if tuple(px) == (0, 0, 0) else pal.index(tuple(px)) + 1 for px in blk.reshape(-1, 3))
            t = self.add_tile(idx)
            bat[ty][tx] = (p << 12) | (0x100 + t)
        return bat

def tile_bytes(idx):
    out = bytearray()
    for y in range(8):
        p0 = p1 = 0
        for x in range(8):
            v = idx[y * 8 + x]
            p0 |= ((v >> 0) & 1) << (7 - x); p1 |= ((v >> 1) & 1) << (7 - x)
        out += bytes([p0, p1])
    for y in range(8):
        p2 = p3 = 0
        for x in range(8):
            v = idx[y * 8 + x]
            p2 |= ((v >> 2) & 1) << (7 - x); p3 |= ((v >> 3) & 1) << (7 - x)
        out += bytes([p2, p3])
    return out

def vce(c):
    r, g, b = c
    return int((int(g) << 6) | (int(r) << 3) | int(b))

# ---------------------------------------------------------------- sprites
class SpriteSheet:
    def __init__(self):
        self.cells = {}   # cell index -> 256 indices
        self.next = 0
        self.pals = {}
    def alloc(self, w, h):
        align = {(16, 16): 1, (32, 16): 2, (16, 32): 4, (32, 32): 4}[(w, h)]
        while self.next % align:
            self.next += 1
        b = self.next
        self.next += {(16, 16): 1, (32, 16): 2, (16, 32): 4, (32, 32): 4}[(w, h)]
        return b
    def put(self, img, palette):
        """img: RGB PIL image (w,h in 16 multiples). palette: list of up to 15 colors (3-bit tuples)."""
        w, h = img.size
        b = self.alloc(w, h)
        qa = q(img)
        for cy in range(h // 16):
            for cx in range(w // 16):
                blk = qa[cy * 16:(cy + 1) * 16, cx * 16:(cx + 1) * 16]
                idx = []
                for px in blk.reshape(-1, 3):
                    t = tuple(px)
                    if t == (0, 0, 0):
                        idx.append(0)
                    else:
                        if t not in palette:
                            raise RuntimeError('sprite color %r not in palette' % (t,))
                        idx.append(palette.index(t) + 1)
                if (w, h) == (16, 32):
                    cell = b + cy * 2
                else:
                    cell = b + cy * (w // 16) + cx
                self.cells[cell] = idx
        return 0x5800 + b * 64   # VRAM word address of pattern

def cell_bytes(idx):
    out = bytearray()
    for plane in range(4):
        for y in range(16):
            v = 0
            for x in range(16):
                v |= ((idx[y * 16 + x] >> plane) & 1) << (15 - x)
            out += bytes([v & 255, v >> 8])
    return out

def spr_img(w, h):
    img = Image.new('RGB', (w, h), (0, 0, 0))
    return img, ImageDraw.Draw(img)

def flipper_frames():
    frames = []
    for s in range(8):
        a = math.radians(28 - s * 52 / 7)
        img, d = spr_img(32, 32)
        px, py = 5, 16
        tx, ty = px + math.cos(a) * FL_LEN, py + math.sin(a) * FL_LEN
        # tapered capsule
        nx, ny = math.sin(a), -math.cos(a)
        r0, r1 = 4.5, 2.5
        poly = [(px + nx * r0, py + ny * r0), (tx + nx * r1, ty + ny * r1),
                (tx - nx * r1, ty - ny * r1), (px - nx * r0, py - ny * r0)]
        d.polygon(poly, fill=C(7, 7, 7))
        d.ellipse((px - r0, py - r0, px + r0, py + r0), fill=C(7, 7, 7))
        d.ellipse((tx - r1, ty - r1, tx + r1, ty + r1), fill=C(7, 7, 7))
        d.line(((px + nx * 1.5, py + ny * 1.5), (tx + nx * 0.5, ty + ny * 0.5)), fill=C(7, 1, 1), width=2)
        d.line(((px - nx * 3, py - ny * 3), (tx - nx * 1.5, ty - ny * 1.5)), fill=C(4, 4, 5))
        d.ellipse((px - 1.5, py - 1.5, px + 1.5, py + 1.5), fill=C(4, 4, 5))
        frames.append(img)
    return frames

def build_sprites():
    sh = SpriteSheet()
    addr = {}
    # ball
    pal_ball = [C2 for C2 in [(7, 7, 7), (5, 5, 6), (3, 3, 4), (1, 1, 2)]]
    img, d = spr_img(16, 16)
    d.ellipse((4, 4, 11, 11), fill=C(3, 3, 4)); d.ellipse((4, 4, 10, 10), fill=C(5, 5, 6))
    d.ellipse((5, 5, 8, 8), fill=C(7, 7, 7)); d.point((10, 10), fill=C(1, 1, 2)); d.point((11, 9), fill=C(1, 1, 2))
    addr['BALL'] = sh.put(img, pal_ball)
    # plunger
    img, d = spr_img(16, 16)
    d.rectangle((3, 0, 12, 3), fill=C(7, 7, 7)); d.rectangle((6, 4, 9, 15), fill=C(5, 5, 6))
    for y in range(5, 16, 3):
        d.line((4, y, 11, y + 1), fill=C(3, 3, 4))
    addr['PLUNGER'] = sh.put(img, pal_ball)
    # flippers
    pal_flip = [(7, 7, 7), (7, 1, 1), (4, 4, 5)]
    fl = flipper_frames()
    addr['FLIP'] = [sh.put(f, pal_flip) for f in fl]
    # eye open (3 pupil positions)
    pal_eye = [(6, 7, 2), (3, 5, 1), (0, 0, 0), (7, 7, 5)]
    eyes = []
    for k, dx in enumerate((-2, 0, 2)):
        img, d = spr_img(16, 16)
        d.ellipse((2, 4, 13, 11), fill=C(3, 5, 1)); d.ellipse((3, 5, 12, 10), fill=C(6, 7, 2))
        d.rectangle((7 + dx, 5, 8 + dx, 10), fill=C(0, 0, 0)); d.point((5, 6), fill=C(7, 7, 5))
        eyes.append(sh.put(img, pal_eye))
    addr['EYE'] = eyes
    # tentacles 16x32 (3 curl frames + stump)
    pal_ten = [(1, 3, 2), (2, 5, 3), (5, 6, 4), (0, 1, 1)]
    tents = []
    for k in range(3):
        img, d = spr_img(16, 32)
        pts = []
        for s in range(12):
            t = s / 11
            px = 8 + math.sin(t * 3.2 + k * 0.9) * 4 * t
            py = 1 + t * 28
            pts.append((px, py, 3.2 - t * 2.2))
        for (px, py, r) in pts:
            d.ellipse((px - r - 0.6, py - r - 0.6, px + r + 0.6, py + r + 0.6), fill=C(0, 1, 1))
        for (px, py, r) in pts:
            d.ellipse((px - r, py - r, px + r, py + r), fill=C(1, 3, 2))
        for (px, py, r) in pts[1::2]:
            d.point((px - 1, py), fill=C(5, 6, 4))
        for (px, py, r) in pts[:8]:
            d.point((px + 1, py - 1), fill=C(2, 5, 3))
        tents.append(sh.put(img, pal_ten))
    img, d = spr_img(16, 32)
    d.ellipse((4, 0, 12, 8), fill=C(1, 3, 2)); d.ellipse((5, 4, 11, 9), fill=C(5, 6, 4))
    tents.append(sh.put(img, pal_ten))
    addr['TENT'] = tents
    # taxi 32x16 + wreck
    pal_taxi = [(7, 6, 0), (5, 4, 0), (1, 2, 3), (7, 7, 7), (0, 0, 0), (7, 3, 0), (3, 3, 3)]
    img, d = spr_img(32, 16)
    d.rounded_rectangle((2, 3, 29, 12), 3, fill=C(7, 6, 0), outline=C(5, 4, 0))
    d.rectangle((9, 4, 13, 11), fill=C(1, 2, 3)); d.rectangle((19, 4, 23, 11), fill=C(1, 2, 3))
    d.rectangle((15, 6, 17, 9), fill=C(7, 7, 7))
    for x in range(4, 28, 2):
        d.point((x, 12 if x % 4 else 3), fill=C(0, 0, 0))
    d.rectangle((27, 4, 28, 5), fill=C(7, 7, 7)); d.rectangle((27, 10, 28, 11), fill=C(7, 7, 7))
    addr['TAXI'] = sh.put(img, pal_taxi)
    img, d = spr_img(32, 16)
    d.polygon([(3, 10), (8, 4), (22, 3), (29, 9), (24, 13), (6, 13)], fill=C(3, 3, 3), outline=C(0, 0, 0))
    d.polygon([(10, 6), (14, 0), (17, 5), (21, 1), (22, 8), (12, 10)], fill=C(7, 3, 0))
    d.polygon([(13, 7), (15, 3), (17, 7), (20, 5), (19, 9)], fill=C(7, 6, 0))
    addr['WRECK'] = sh.put(img, pal_taxi)
    # tank 32x32 (barrel up)
    pal_tank = [(2, 3, 1), (1, 2, 0), (3, 4, 2), (0, 0, 0), (4, 4, 3)]
    img, d = spr_img(32, 32)
    d.rectangle((5, 12, 10, 30), fill=C(1, 2, 0)); d.rectangle((21, 12, 26, 30), fill=C(1, 2, 0))
    for y in range(13, 30, 3):
        d.line((5, y, 10, y), fill=C(0, 0, 0)); d.line((21, y, 26, y), fill=C(0, 0, 0))
    d.rectangle((9, 14, 22, 28), fill=C(2, 3, 1), outline=C(1, 2, 0))
    d.ellipse((11, 15, 20, 24), fill=C(3, 4, 2), outline=C(1, 2, 0))
    d.rectangle((14, 1, 17, 18), fill=C(4, 4, 3), outline=C(1, 2, 0))
    d.point((15, 22), fill=C(4, 4, 3))
    addr['TANK'] = sh.put(img, pal_tank)
    # shell
    pal_fx = [(7, 7, 5), (7, 6, 1), (7, 3, 0), (5, 1, 0), (2, 0, 0)]
    img, d = spr_img(16, 16)
    d.ellipse((5, 2, 10, 9), fill=C(7, 6, 1)); d.ellipse((6, 3, 9, 7), fill=C(7, 7, 5))
    d.line((7, 10, 7, 15), fill=C(7, 3, 0)); d.line((8, 10, 8, 13), fill=C(5, 1, 0))
    addr['SHELL'] = sh.put(img, pal_fx)
    # explosion 2 frames
    exps = []
    for k in range(2):
        img, d = spr_img(32, 32)
        rr = 9 + k * 5
        for i in range(10):
            a = i * math.pi / 5 + k * 0.3
            d.ellipse((16 + math.cos(a) * rr - 5, 16 + math.sin(a) * rr - 5,
                       16 + math.cos(a) * rr + 5, 16 + math.sin(a) * rr + 5), fill=C(5, 1, 0) if k else C(7, 3, 0))
        d.ellipse((16 - rr, 16 - rr, 16 + rr, 16 + rr), fill=C(7, 3, 0) if k else C(7, 6, 1))
        d.ellipse((16 - rr + 4, 16 - rr + 4, 16 + rr - 4, 16 + rr - 4), fill=C(7, 6, 1) if k else C(7, 7, 5))
        exps.append(sh.put(img, pal_fx))
    addr['EXPL'] = exps
    # fireballs (2 frames)
    fires = []
    for k in range(2):
        img, d = spr_img(16, 16)
        d.ellipse((3, 5 - k, 12, 14), fill=C(7, 3, 0)); d.ellipse((5, 7, 10, 12), fill=C(7, 6, 1))
        d.polygon([(4, 7), (8, 0 + k * 2), (11, 7)], fill=C(7, 3, 0)); d.point((7, 9), fill=C(7, 7, 5))
        fires.append(sh.put(img, pal_fx))
    addr['FIRE'] = fires
    # subway train (side view) 32x16 front + car
    pal_train = [(5, 5, 6), (3, 3, 4), (1, 1, 2), (7, 7, 5), (7, 1, 1), (0, 0, 0)]
    trains = []
    for front in (1, 0):
        img, d = spr_img(32, 16)
        d.rectangle((0, 2, 31, 13), fill=C(5, 5, 6), outline=C(1, 1, 2))
        d.line((0, 10, 31, 10), fill=C(7, 1, 1))
        for x in range(3, 28, 7):
            d.rectangle((x, 4, x + 4, 8), fill=C(7, 7, 5) if front else C(1, 1, 2))
        if front:
            d.rectangle((27, 3, 31, 12), fill=C(3, 3, 4)); d.rectangle((29, 5, 31, 7), fill=C(7, 7, 5))
        d.ellipse((4, 12, 8, 15), fill=C(0, 0, 0)); d.ellipse((22, 12, 26, 15), fill=C(0, 0, 0))
        trains.append(sh.put(img, pal_train))
    addr['TRAIN'] = trains
    # cultists 16x32 (2 walk frames)
    pal_cult = [(3, 0, 3), (2, 0, 2), (5, 1, 5), (3, 7, 2), (0, 0, 0), (6, 5, 4)]
    cults = []
    for k in range(2):
        img, d = spr_img(16, 32)
        d.polygon([(8, 3), (3, 12), (2, 30), (14, 30), (13, 12)], fill=C(3, 0, 3), outline=C(2, 0, 2))
        d.ellipse((4, 2, 12, 12), fill=C(2, 0, 2)); d.ellipse((5, 5, 11, 11), fill=C(0, 0, 0))
        d.point((7, 8), fill=C(3, 7, 2)); d.point((9, 8), fill=C(3, 7, 2))
        d.line((8, 12, 8, 29), fill=C(5, 1, 5))
        d.rectangle((3 + k * 6, 29, 6 + k * 6, 31), fill=C(0, 0, 0))
        d.line((3, 16, 0, 22 - k * 3), fill=C(3, 0, 3), width=2); d.line((13, 16, 15, 22 + k * 3 - 3), fill=C(3, 0, 3), width=2)
        d.point((0, 22 - k * 3), fill=C(6, 5, 4))
        cults.append(sh.put(img, pal_cult))
    addr['CULT'] = cults
    # big eyes 32x32: open, hurt, destroyed
    pal_beye = [(6, 7, 2), (3, 5, 1), (0, 0, 0), (7, 7, 5), (7, 1, 1), (1, 2, 1), (2, 4, 2)]
    beyes = []
    for st in range(3):
        img, d = spr_img(32, 32)
        if st < 2:
            d.ellipse((1, 6, 30, 25), fill=C(1, 2, 1))
            d.ellipse((3, 8, 28, 23), fill=C(3, 5, 1) if st == 0 else C(7, 1, 1))
            d.ellipse((5, 9, 26, 22), fill=C(6, 7, 2) if st == 0 else C(7, 1, 1))
            d.ellipse((13, 9, 18, 22), fill=C(0, 0, 0)); d.point((9, 12), fill=C(7, 7, 5)); d.point((10, 12), fill=C(7, 7, 5))
        else:
            d.ellipse((1, 6, 30, 25), fill=C(1, 2, 1)); d.line((4, 16, 27, 16), fill=C(2, 4, 2), width=2)
            d.line((8, 10, 23, 22), fill=C(7, 1, 1), width=2); d.line((23, 10, 8, 22), fill=C(7, 1, 1), width=2)
        beyes.append(sh.put(img, pal_beye))
    addr['BIGEYE'] = beyes
    pals = {'TRAIN': pal_train, 'CULT': pal_cult, 'BIGEYE': pal_beye,
            'BALL': pal_ball, 'FLIP': pal_flip, 'EYE': pal_eye, 'TENT': pal_ten,
            'TENTHIT': [(7, 1, 1), (7, 4, 3), (7, 7, 5), (2, 0, 0)],
            'TAXI': pal_taxi, 'TANK': pal_tank, 'FX': pal_fx}
    return sh, addr, pals

# ---------------------------------------------------------------- main
def main():
    mat = build_mat()
    grid = build_collision(mat)
    open(os.path.join(OUT, 'coll.bin'), 'wb').write(grid.tobytes())

    art = draw_table(mat, False)
    art_v = draw_table(mat, True)
    title = draw_title()
    art.save(os.path.join(PREV, 'table.png')); art_v.save(os.path.join(PREV, 'table_variant.png'))
    title.save(os.path.join(PREV, 'title.png'))
    # collision preview
    cp = np.zeros((H // 2, W // 2, 3), np.uint8)
    matcol = {1: (120, 120, 140), 2: (255, 60, 60), 3: (255, 0, 255), 4: (0, 200, 80), 5: (255, 200, 0)}
    for m, col in matcol.items():
        cp[(grid >> 5) == m] = col
    Image.fromarray(cp).resize((W, H), Image.NEAREST).save(os.path.join(PREV, 'collision.png'))

    pool = TilePool(reserved_pals=[13, 14, 15])
    # font tiles first (tile 0 = space)
    font_tiles = []
    for ch in CHARS:
        g = GLYPHS[ch]
        idx = [0] * 64
        for ry in range(7):
            for rx in range(5):
                if g[ry][rx] == '1':
                    idx[ry * 8 + rx + 1] = 1
                    if ry + 1 < 8 and rx + 2 < 8 and idx[(ry + 1) * 8 + rx + 2] == 0:
                        idx[(ry + 1) * 8 + rx + 2] = 2
        for ry in range(7):
            for rx in range(5):
                if g[ry][rx] == '1':
                    idx[ry * 8 + rx + 1] = 1
        font_tiles.append(pool.add_tile(tuple(idx)))
    assert font_tiles[0] == 0
    bat = np.full((64, 64), 0x100, np.int64)
    qt = q(art)
    tb = pool.convert(qt, 0, 0, 32, 64)
    bat[0:64, 0:32] = np.array(tb)
    tt = pool.convert(q(title), 0, 0, 32, 28)
    bat[4:32, 32:64] = np.array(tt)
    # variants: convert full variant image but only keep regions
    qv = q(art_v)
    def var_region(c0, r0, cw, rh):
        sub = qv[r0 * 8:(r0 + rh) * 8, c0 * 8:(c0 + cw) * 8]
        vb = pool.convert(sub, 0, 0, cw, rh)
        return [v for row in vb for v in row], [int(bat[r0 + y, c0 + x]) for y in range(rh) for x in range(cw)]
    variants = {}
    variants['TARGET'] = [var_region(11 + i * 3, 40, 2, 1) for i in range(3)]
    variants['BUMP'] = [var_region(9, 23, 4, 4), var_region(16, 23, 4, 4), var_region(13, 28, 3, 4)]
    variants['EMPIRE'] = [var_region(26, 34 - l, 2, 1) for l in range(5)]
    variants['TORCH'] = [var_region(4, 55, 2, 2)]
    ntiles = len(pool.tiles)
    print('unique BG tiles:', ntiles, 'palettes used:', [len(p) for p in pool.pals])
    # font palettes
    pool.pals[13] = [(5, 7, 2), (1, 2, 0)]
    pool.pals[14] = [(7, 7, 7), (2, 2, 3)]
    pool.pals[15] = [(7, 6, 1), (3, 1, 0)]
    chr_data = b''.join(tile_bytes(t) for t in pool.tiles)
    open(os.path.join(OUT, 'bg_chr.bin'), 'wb').write(chr_data)
    open(os.path.join(OUT, 'bg_bat.bin'), 'wb').write(b''.join(int(v).to_bytes(2, 'little') for v in bat.flatten()))
    pal = bytearray()
    for p in range(16):
        cols = [(0, 0, 0)] + pool.pals[p] + [(0, 0, 0)] * (15 - len(pool.pals[p]))
        for c in cols:
            pal += vce(c).to_bytes(2, 'little')
    open(os.path.join(OUT, 'bg_pal.bin'), 'wb').write(pal)

    sh, saddr, spals = build_sprites()
    ncell = sh.next
    print('sprite cells:', ncell)
    sdata = bytearray()
    for c in range(ncell):
        sdata += cell_bytes(sh.cells.get(c, [0] * 256))
    open(os.path.join(OUT, 'spr_chr.bin'), 'wb').write(sdata)
    spal_order = ['BALL', 'FLIP', 'EYE', 'TENT', 'TENTHIT', 'TAXI', 'TANK', 'FX', 'TRAIN', 'CULT', 'BIGEYE']
    sp = bytearray()
    for name in spal_order:
        cols = [(0, 0, 0)] + spals[name] + [(0, 0, 0)] * (15 - len(spals[name]))
        for c in cols:
            sp += vce(c).to_bytes(2, 'little')
    open(os.path.join(OUT, 'spr_pal.bin'), 'wb').write(sp)

    # ---------------- bonus rooms
    import rooms
    Hns = sys.modules[__name__]
    M = {'WALL': MAT_WALL, 'SLING': MAT_SLING, 'BUMP': MAT_BUMP, 'BOSS': MAT_BOSS, 'EMPIRE': MAT_EMPIRE}
    room_defs = []
    for kind in (1, 2, 3):
        rmat = rooms.build_room_mat(kind, M)
        rgrid = build_collision(rmat)
        open(os.path.join(OUT, 'room%d_coll.bin' % kind), 'wb').write(rgrid.tobytes())
        rimg = rooms.draw_room(kind, rmat, Hns, 0)
        rimg.save(os.path.join(PREV, 'room%d.png' % kind))
        rp = TilePool(reserved_pals=[13, 14, 15])
        for t in pool.tiles[:len(CHARS)]:
            rp.add_tile(t)
        rb = rp.convert(q(rimg), 0, 0, 32, 26)
        rvars = []
        if kind == 1:
            qv1 = q(rooms.draw_room(kind, rmat, Hns, 1))
            for (x, y) in rooms.SWITCHES:
                c0 = x // 8
                vb = rp.convert(qv1[8:16, c0 * 8:(c0 + 2) * 8], 0, 0, 2, 1)
                rvars.append([v for row in vb for v in row])
        if kind == 3:
            for v in (1, 2):
                qv = q(rooms.draw_room(kind, rmat, Hns, v))
                vb = rp.convert(qv[16:56, 96:160], 0, 0, 8, 5)
                rvars.append([vv for row in vb for vv in row])
            rooms.draw_room(kind, rmat, Hns, 2).save(os.path.join(PREV, 'room3_destroyed.png'))
        print('room', kind, 'tiles', len(rp.tiles) - len(CHARS), 'pals', [len(p) for p in rp.pals[:13]])
        rchr = b''.join(tile_bytes(t) for t in rp.tiles[len(CHARS):])
        open(os.path.join(OUT, 'room%d_chr.bin' % kind), 'wb').write(rchr)
        open(os.path.join(OUT, 'room%d_bat.bin' % kind), 'wb').write(b''.join(int(v).to_bytes(2, 'little') for row in rb for v in row))
        rpal = bytearray()
        for p in range(13):
            cols = [(0, 0, 0)] + rp.pals[p] + [(0, 0, 0)] * (15 - len(rp.pals[p]))
            for c in cols:
                rpal += vce(c).to_bytes(2, 'little')
        open(os.path.join(OUT, 'room%d_pal.bin' % kind), 'wb').write(rpal)
        room_defs.append((kind, len(rchr) // 2, rvars))

    # ---------------- gen.h
    L = []
    L.append('#define FONT_TILES %d' % len(CHARS))
    for (kind, words, rvars) in room_defs:
        L.append('#define ROOM%d_CHR_WORDS %d' % (kind, words))
        if rvars:
            L.append('const unsigned int ROOM%d_VAR[] = { %s };' % (kind, ', '.join('0x%04x' % v for vs in rvars for v in vs)))
    L.append('#define RLPX %d\n#define RLPY %d\n#define RRPX %d' % (rooms.RLP + (rooms.RRP[0],)))
    for i, (x, y) in enumerate(rooms.ROOF_EYES):
        L.append('#define REYE%d_X %d\n#define REYE%d_Y %d' % (i, x, i, y))
    L.append('/* generated by tools/gen_assets.py -- do not edit */')
    L.append('#define BG_CHR_WORDS %d' % (len(chr_data) // 2))
    L.append('#define SPR_WORDS %d' % (len(sdata) // 2))
    L.append('#define SPR_NPAL %d' % len(spal_order))
    for i, n in enumerate(spal_order):
        L.append('#define SP_%s %d' % (n, i))
    for k, v in saddr.items():
        if isinstance(v, list):
            L.append('const unsigned int SPR_%s[] = { %s };' % (k, ', '.join('0x%04x' % a for a in v)))
        else:
            L.append('#define SPR_%s 0x%04x' % (k, v))
    # font map: ASCII -> BAT entry (palette added at runtime)
    fm = [0x100] * 96
    for i, ch in enumerate(CHARS):
        fm[ord(ch) - 32] = 0x100 + font_tiles[i]
    for ch in 'abcdefghijklmnopqrstuvwyz':
        fm[ord(ch) - 32] = fm[ord(ch.upper()) - 32]
    L.append('const unsigned int FONT[] = { %s };' % ', '.join('0x%03x' % v for v in fm))
    for name, lst in variants.items():
        on = [v for (a, b) in lst for v in a]; off = [v for (a, b) in lst for v in b]
        L.append('const unsigned int VAR_%s_ON[] = { %s };' % (name, ', '.join('0x%04x' % v for v in on)))
        L.append('const unsigned int VAR_%s_OFF[] = { %s };' % (name, ', '.join('0x%04x' % v for v in off)))
    L.append('const unsigned char VAR_BUMP_POS[] = { 9,23,4,4, 16,23,4,4, 13,28,3,4 };')
    # normals
    nx = [int(round(math.cos(k * 2 * math.pi / 32) * 64)) for k in range(32)]
    ny = [int(round(math.sin(k * 2 * math.pi / 32) * 64)) for k in range(32)]
    L.append('const int NX[] = { %s };' % ', '.join(map(str, nx)))
    L.append('const int NY[] = { %s };' % ', '.join(map(str, ny)))
    # flipper tables (left; right mirrors x)
    fdx, fdy, fnx, fny = [], [], [], []
    for s in range(8):
        a = math.radians(28 - s * 52 / 7)
        fdx.append(int(round(math.cos(a) * 64))); fdy.append(int(round(math.sin(a) * 64)))
        fnx.append(int(round(math.sin(a) * 64))); fny.append(int(round(-math.cos(a) * 64)))
    for n, arr in (('FDX', fdx), ('FDY', fdy), ('FNX', fnx), ('FNY', fny)):
        L.append('const int %s[] = { %s };' % (n, ', '.join(map(str, arr))))
    sin = [int(round(math.sin(i * 2 * math.pi / 64) * 64)) for i in range(64)]
    L.append('const signed char SINT[] = { %s };' % ', '.join(map(str, sin)))
    L.append('#define LPX %d\n#define LPY %d\n#define RPX %d\n#define RPY %d\n#define FL_LEN %d' % (LP + RP + (FL_LEN,)))
    for i, (bx, by) in enumerate(BUMPERS):
        L.append('#define BUMP%d_X %d\n#define BUMP%d_Y %d' % (i, bx, i, by))
    for i, (tx, ty) in enumerate(TARGETS):
        L.append('#define TGT%d_X %d' % (i, tx))
    L.append('#define TGT_Y %d' % TARGETS[0][1])
    L.append('#define SUBWAY_X %d\n#define SUBWAY_Y %d' % SUBWAY)
    def color_slots(c):
        out = []
        for p in range(13):
            if c in pool.pals[p]:
                out.append(p * 16 + pool.pals[p].index(c) + 1)
        return out
    wing = color_slots((2, 0, 2)) + color_slots((4, 1, 4))
    L.append('const unsigned int WING_SLOTS[] = { %s };' % ', '.join(map(str, wing)))
    L.append('#define N_WING_SLOTS %d' % len(wing))
    worig = [vce((2, 0, 2))] * len(color_slots((2, 0, 2))) + [vce((4, 1, 4))] * len(color_slots((4, 1, 4)))
    L.append('const unsigned int WING_ORIG[] = { %s };' % ', '.join(map(str, worig)))
    print('wing color slots', wing)
    def wrap(line):
        if len(line) < 200: return line
        head, body = line.split('{', 1)
        items = body.rsplit('}', 1)[0].split(',')
        rows = [','.join(items[i:i+12]) for i in range(0, len(items), 12)]
        return head + '{\n' + ',\n'.join(rows) + '\n};'
    open(os.path.join(OUT, 'gen.h'), 'w').write('\n'.join(wrap(x) for x in L) + '\n')
    if ntiles > 1536:
        print('WARNING: too many tiles!')

if __name__ == '__main__':
    main()
