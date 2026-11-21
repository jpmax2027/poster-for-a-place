#!/usr/bin/env python3
"""SOLVARA — a travel poster for a place that isn't there.

Writes one PNG image to $MAKEFUN_OUTPUT_DIR/entry.png (default /output):
a vintage travel poster for Solvara, the island that refused to sink —
a floating island above a dawn sea, waterfalls spilling off its rim,
a white lighthouse on its meadow, and its name set large across the sky.

Pure Python 3.13 standard library. No network. Fully deterministic:
two runs produce byte-identical output. Renders supersampled x2 and
box-downsamples for smooth edges, with a light print grain and a
posterised palette so the PNG stays well under the 1 MiB gate.
"""

import math
import os
import struct
import zlib

# ---------------------------------------------------------------- canvas

W, H = 864, 1024          # final image size
SS = 2                    # supersampling factor
SW, SH = W * SS, H * SS   # render size

buf = bytearray(SW * SH * 3)


def _set(x, y, rgb):
    i = (y * SW + x) * 3
    buf[i] = rgb[0]
    buf[i + 1] = rgb[1]
    buf[i + 2] = rgb[2]


def fill_rect(x, y, w, h, rgb):
    """Axis-aligned rectangle in final-image coordinates."""
    x0, y0 = int(x * SS), int(y * SS)
    x1, y1 = int((x + w) * SS), int((y + h) * SS)
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(SW, x1)
    y1 = min(SH, y1)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(rgb) * (x1 - x0)
    n = len(row)
    for yy in range(y0, y1):
        i = (yy * SW + x0) * 3
        buf[i:i + n] = row


def fill_polygon(paths, rgb):
    """Fill one or more closed paths with the even-odd rule.

    Each path is a list of (x, y) points in final-image coordinates.
    Combining an outer path with an inner path punches a hole.
    """
    scaled = [[(px * SS, py * SS) for (px, py) in path] for path in paths]
    ymin = min(p[1] for path in scaled for p in path)
    ymax = max(p[1] for path in scaled for p in path)
    y0 = max(0, int(math.floor(ymin)))
    y1 = min(SH - 1, int(math.ceil(ymax)))
    edges = []
    for path in scaled:
        n = len(path)
        for i in range(n):
            ax, ay = path[i]
            bx, by = path[(i + 1) % n]
            if ay != by:
                edges.append((ax, ay, bx, by))
    r, g, b = rgb
    for yy in range(y0, y1 + 1):
        yc = yy + 0.5
        xs = []
        for (ax, ay, bx, by) in edges:
            if (ay <= yc < by) or (by <= yc < ay):
                xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        if len(xs) < 2:
            continue
        xs.sort()
        base = yy * SW * 3
        for k in range(0, len(xs) - 1, 2):
            xa = max(0, int(math.ceil(xs[k] - 0.5)))
            xb = min(SW - 1, int(math.floor(xs[k + 1] - 0.5)))
            if xb < xa:
                continue
            i = base + xa * 3
            j = base + (xb + 1) * 3
            buf[i:j] = _span(buf[i:j], r, g, b)


def _span(seg, r, g, b):
    out = bytearray(len(seg))
    out[0::3] = bytes([r]) * (len(seg) // 3)
    out[1::3] = bytes([g]) * (len(seg) // 3)
    out[2::3] = bytes([b]) * (len(seg) // 3)
    return bytes(out)


def ellipse_path(cx, cy, rx, ry, seg=56):
    return [(cx + rx * math.cos(2 * math.pi * i / seg),
             cy + ry * math.sin(2 * math.pi * i / seg)) for i in range(seg)]


def fill_ellipse(cx, cy, rx, ry, rgb):
    fill_polygon([ellipse_path(cx, cy, rx, ry)], rgb)


def fill_circle(cx, cy, rad, rgb):
    fill_ellipse(cx, cy, rad, rad, rgb)


def arc_points(cx, cy, rx, ry, a0, a1, step=5.0):
    """Points along an elliptical arc, angles in degrees."""
    pts = []
    n = max(2, int(abs(a1 - a0) / step) + 1)
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


def lerp(c0, c1, t):
    return (int(c0[0] + (c1[0] - c0[0]) * t),
            int(c0[1] + (c1[1] - c0[1]) * t),
            int(c0[2] + (c1[2] - c0[2]) * t))


def v_gradient(x, y, w, h, stops):
    """Vertical multi-stop gradient. stops: [(pos0..1, rgb), ...]"""
    rows = int(h * SS)
    x0 = int(x * SS)
    wid = int(w * SS)
    rowcache = {}
    for j in range(rows):
        t = j / max(1, rows - 1)
        for s in range(len(stops) - 1):
            p0, c0 = stops[s]
            p1, c1 = stops[s + 1]
            if p0 <= t <= p1:
                rgb = lerp(c0, c1, (t - p0) / max(1e-9, p1 - p0))
                break
        else:
            rgb = stops[-1][1]
        if rgb not in rowcache:
            rowcache[rgb] = bytes(rgb) * wid
        yy = int(y * SS) + j
        if 0 <= yy < SH:
            i = (yy * SW + x0) * 3
            buf[i:i + wid * 3] = rowcache[rgb]


def blend(c0, c1, t):
    """Colour c1 mixed over c0 by t (for pre-mixed 'translucent' paint)."""
    return lerp(c0, c1, t)

# ---------------------------------------------------------------- palette

CREAM = (243, 233, 210)
IVORY = (247, 240, 220)
GOLD = (217, 164, 65)
GOLD_DEEP = (201, 138, 44)
CORAL = (200, 85, 61)
TEAL_DEEP = (23, 63, 77)
TEAL_DARK = (15, 46, 58)
INK = (24, 42, 46)
SUN = (246, 199, 107)
SUN_HALO = (240, 176, 96)
SKY_A = (31, 78, 95)
SKY_B = (78, 126, 134)
SKY_C = (233, 168, 123)
SKY_D = (246, 217, 168)
CLOUD = (244, 222, 182)
MEADOW = (102, 133, 79)
MEADOW_DARK = (79, 107, 60)
ROCK = (51, 65, 62)
ROCK_LIGHT = (74, 92, 84)
ROCK_WARM = (232, 144, 111)
PINE = (34, 58, 48)
FALL = (207, 232, 223)
FALL_CORE = (240, 248, 240)
SEA_STREAK = (44, 99, 115)
SHADOW = (11, 37, 48)

# ---------------------------------------------------------------- letters
# Glyphs live in a 100 x 140 box, drawn as filled shapes (final coords
# are produced by placing each glyph with an origin and a scale).

def draw_S(ox, oy, s, rgb):
    pts = arc_points(50, 41, 30, 30, -55, -270, 5.0)
    pts += arc_points(50, 99, 30, 30, -90, 140, 5.0)
    pts = [(ox + px * s, oy + py * s) for (px, py) in pts]
    _stroke(pts, 25 * s, rgb)


def _stroke(pts, width, rgb):
    half = width / 2.0
    left, right = [], []
    n = len(pts)
    for i in range(n):
        px, py = pts[i]
        if i == 0:
            dx, dy = pts[1][0] - px, pts[1][1] - py
        elif i == n - 1:
            dx, dy = px - pts[i - 1][0], py - pts[i - 1][1]
        else:
            dx = pts[i + 1][0] - pts[i - 1][0]
            dy = pts[i + 1][1] - pts[i - 1][1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d, dx / d
        left.append((px + nx * half, py + ny * half))
        right.append((px - nx * half, py - ny * half))
    fill_polygon([left + right[::-1]], rgb)
    for (px, py) in pts:
        fill_circle(px, py, half, rgb)


def draw_O(ox, oy, s, rgb):
    outer = ellipse_path(ox + 50 * s, oy + 70 * s, 49 * s, 69 * s)
    inner = ellipse_path(ox + 50 * s, oy + 70 * s, 24 * s, 43 * s)
    fill_polygon([outer, inner], rgb)


def draw_L(ox, oy, s, rgb):
    pts = [(0, 0), (36, 0), (36, 104), (100, 104), (100, 140), (0, 140)]
    fill_polygon([[(ox + px * s, oy + py * s) for (px, py) in pts]], rgb)


def draw_V(ox, oy, s, rgb):
    pts = [(0, 0), (37, 0), (50, 100), (63, 0), (100, 0), (68, 140), (32, 140)]
    fill_polygon([[(ox + px * s, oy + py * s) for (px, py) in pts]], rgb)


def draw_A(ox, oy, s, rgb):
    outer = [(0, 140), (38, 0), (62, 0), (100, 140), (73, 140),
             (64, 100), (36, 100), (27, 140)]
    hole = [(50, 36), (59, 82), (41, 82)]
    fill_polygon([[(ox + px * s, oy + py * s) for (px, py) in outer],
                  [(ox + px * s, oy + py * s) for (px, py) in hole]], rgb)


def draw_R(ox, oy, s, rgb):
    bar = [(0, 0), (35, 0), (35, 140), (0, 140)]
    fill_polygon([[(ox + px * s, oy + py * s) for (px, py) in bar]], rgb)
    bowl = arc_points(38, 42, 38, 30, -90, 90, 5.0)
    bowl = [(ox + px * s, oy + py * s) for (px, py) in bowl]
    _stroke(bowl, 25 * s, rgb)
    leg = [(38, 70), (74, 70), (100, 140), (63, 140), (28, 80)]
    fill_polygon([[(ox + px * s, oy + py * s) for (px, py) in leg]], rgb)


GLYPHS = {'S': draw_S, 'O': draw_O, 'L': draw_L,
          'V': draw_V, 'A': draw_A, 'R': draw_R}


def draw_word(word, cx, oy, scale, rgb, tracking=16):
    total = len(word) * 100 * scale + (len(word) - 1) * tracking * scale
    x = cx - total / 2.0
    for ch in word:
        GLYPHS[ch](x, oy, scale, rgb)
        x += (100 + tracking) * scale

# ---------------------------------------------------------------- scene

IX, IY, IW, IH = 26, 26, W - 52, H - 52   # inner picture area


def cloud(cx, cy, w, rgb):
    fill_ellipse(cx, cy, w * 0.50, w * 0.16, rgb)
    fill_ellipse(cx - w * 0.26, cy + w * 0.03, w * 0.30, w * 0.12, rgb)
    fill_ellipse(cx + w * 0.27, cy + w * 0.02, w * 0.32, w * 0.13, rgb)
    fill_ellipse(cx + w * 0.02, cy - w * 0.07, w * 0.30, w * 0.13, rgb)


def pine(x, ybase, h, rgb):
    w = h * 0.42
    fill_polygon([[(x, ybase - h), (x - w / 2, ybase - h * 0.35),
                   (x + w / 2, ybase - h * 0.35)]], rgb)
    fill_polygon([[(x, ybase - h * 0.78), (x - w * 0.58, ybase - h * 0.08),
                   (x + w * 0.58, ybase - h * 0.08)]], rgb)
    fill_rect(x - 2.5, ybase - h * 0.12, 5, h * 0.12, rgb)


def house(x, ybase, w, wall, roof):
    h = w * 0.72
    fill_rect(x, ybase - h, w, h, wall)
    fill_polygon([[(x - w * 0.12, ybase - h), (x + w * 0.5, ybase - h * 1.55),
                   (x + w * 1.12, ybase - h)]], roof)
    fill_rect(x + w * 0.38, ybase - h * 0.52, w * 0.24, h * 0.52, INK)
    fill_rect(x + w * 0.10, ybase - h * 0.78, w * 0.18, h * 0.24, SUN)
    fill_rect(x + w * 0.72, ybase - h * 0.78, w * 0.18, h * 0.24, SUN)


def draw_scene():
    # paper
    fill_rect(0, 0, W, H, CREAM)
    # sky
    v_gradient(IX, IY, IW, 700 - IY, [(0.0, SKY_A), (0.38, SKY_B),
                                      (0.72, SKY_C), (1.0, SKY_D)])
    # sun halo + disc, low behind the island
    fill_circle(432, 566, 186, blend(SKY_C, SUN_HALO, 0.55))
    fill_circle(432, 566, 158, SUN)
    # clouds
    cloud(168, 316, 190, blend(SKY_B, CLOUD, 0.5))
    cloud(706, 262, 160, blend(SKY_B, CLOUD, 0.45))
    cloud(664, 428, 210, blend(SKY_C, CLOUD, 0.55))
    cloud(150, 470, 130, blend(SKY_C, CLOUD, 0.5))
    # sea
    v_gradient(IX, 700, IW, IY + IH - 700,
               [(0.0, (38, 92, 102)), (0.25, TEAL_DEEP), (1.0, TEAL_DARK)])
    # island shadow on the water
    fill_ellipse(432, 892, 205, 26, SHADOW)
    fill_ellipse(432, 892, 150, 18, blend(SHADOW, TEAL_DARK, 0.35))
    # sun glitter path on the sea
    for i, yy in enumerate(range(716, 896, 15)):
        halfw = 66 - i * 3
        off = ((i * 37) % 23) - 11
        fill_rect(432 - halfw + off, yy, halfw * 1.5, 5,
                  blend(TEAL_DEEP, SUN, 0.55 - i * 0.03))
    # sea streaks (deterministic dashes)
    for i in range(46):
        yy = 724 + (i * 53) % 250
        xx = IX + 14 + (i * 197) % (IW - 150)
        ln = 34 + (i * 29) % 60
        fill_rect(xx, yy, ln, 4, blend(TEAL_DARK, SEA_STREAK, 0.7))
    # waterfalls (behind the island's front rim, falling to the sea)
    for fx, fw in ((322, 17), (528, 14)):
        fill_polygon([[(fx, 470), (fx + fw, 470), (fx + fw - 3, 884),
                       (fx + 3, 884)]], FALL)
        fill_rect(fx + fw * 0.32, 480, fw * 0.34, 398, FALL_CORE)
        for k in range(5):  # foam
            fill_ellipse(fx + fw / 2 + (k - 2) * 13, 888 + (k % 2) * 5,
                         13 - (k % 2) * 3, 6, FALL_CORE)
    # the floating island: rock body
    rock = [(248, 468), (616, 468), (566, 636), (478, 756),
            (432, 806), (386, 756), (298, 636)]
    fill_polygon([rock], ROCK)
    # rock strata
    fill_polygon([[(272, 540), (592, 540), (566, 636), (520, 690),
                   (330, 690), (298, 636)]], ROCK_LIGHT)
    fill_polygon([[(330, 690), (520, 690), (478, 756), (432, 806),
                   (386, 756)]], ROCK)
    # warm rim light on the sun side
    fill_polygon([[(616, 468), (566, 636), (478, 756), (462, 724),
                   (540, 622), (580, 470)]], ROCK_WARM)
    # meadow cap
    fill_polygon([[(248, 470), (300, 442), (564, 442), (616, 470),
                   (616, 488), (248, 488)]], MEADOW)
    fill_polygon([[(248, 478), (616, 478), (616, 488), (248, 488)]],
                 MEADOW_DARK)
    # pines on the meadow
    pine(300, 452, 64, PINE)
    pine(338, 448, 46, PINE)
    pine(598, 454, 56, PINE)
    # houses
    house(368, 452, 52, IVORY, CORAL)
    house(428, 448, 40, (238, 220, 188), TEAL_DEEP)
    # lighthouse
    lx, lbase = 512, 450
    fill_polygon([[(lx, lbase), (lx + 15, lbase - 74),
                   (lx + 37, lbase - 74), (lx + 52, lbase)]], IVORY)
    fill_polygon([[(lx + 8, lbase - 30), (lx + 44, lbase - 30),
                   (lx + 41, lbase - 46), (lx + 11, lbase - 46)]], CORAL)
    fill_rect(lx + 13, lbase - 92, 26, 18, INK)               # lamp room
    fill_circle(lx + 26, lbase - 83, 6, SUN)                  # lamp
    fill_polygon([[(lx + 8, lbase - 92), (lx + 26, lbase - 106),
                   (lx + 44, lbase - 92)]], CORAL)            # roof
    # light beam, pre-blended over the sky tone it crosses
    beam = [(lx + 40, lbase - 86), (lx + 208, lbase - 128),
            (lx + 208, lbase - 62)]
    fill_polygon([beam], blend(SKY_C, (250, 226, 160), 0.45))
    # birds
    for (bx, by, bs) in ((196, 356, 15), (648, 330, 12), (566, 292, 10)):
        pts = arc_points(bx - bs, by, bs, bs * 0.55, 200, 330, 9.0)
        pts += arc_points(bx + bs, by, bs, bs * 0.55, 210, 340, 9.0)
        _stroke(pts, 3.2, INK)
    # the name, set into the sky: shadow pass, then ivory
    draw_word('SOLVARA', 437, 104, 0.99, TEAL_DARK, 15)
    draw_word('SOLVARA', 432, 98, 0.99, IVORY, 15)
    # ornamental divider under the name
    fill_rect(316, 268, 236, 5, GOLD_DEEP)
    fill_polygon([[(432, 258), (444, 270), (432, 282), (420, 270)]], GOLD_DEEP)
    # vintage double frame
    fill_rect(0, 0, W, 10, GOLD_DEEP)
    fill_rect(0, H - 10, W, 10, GOLD_DEEP)
    fill_rect(0, 0, 10, H, GOLD_DEEP)
    fill_rect(W - 10, 0, 10, H, GOLD_DEEP)
    fill_rect(16, 16, W - 32, 3, CORAL)
    fill_rect(16, H - 19, W - 32, 3, CORAL)
    fill_rect(16, 16, 3, H - 32, CORAL)
    fill_rect(W - 19, 16, 3, H - 32, CORAL)

# ---------------------------------------------------------------- finish

def finish():
    """Downsample x2, add deterministic grain + vignette, posterise."""
    out = bytearray(W * H * 3)
    for y in range(H):
        for x in range(W):
            r = g = b = 0
            base = ((y * SS) * SW + x * SS) * 3
            for dy in range(SS):
                i = base + dy * SW * 3
                for dx in range(SS):
                    j = i + dx * 3
                    r += buf[j]
                    g += buf[j + 1]
                    b += buf[j + 2]
            n = SS * SS
            r //= n
            g //= n
            b //= n
            # deterministic grain, +-5
            hsh = (x * 374761393 + y * 668265263) & 0xFFFFFFFF
            hsh = (hsh ^ (hsh >> 13)) * 1274126177 & 0xFFFFFFFF
            grain = ((hsh >> 8) % 11) - 5
            # gentle vignette
            vx = (x - W / 2) / (W / 2)
            vy = (y - H / 2) / (H / 2)
            d2 = vx * vx + vy * vy
            shade = 1.0 - 0.16 * max(0.0, d2 - 0.55)
            r = int((r + grain) * shade)
            g = int((g + grain) * shade)
            b = int((b + grain) * shade)
            # posterise to steps of 4 (keeps the PNG small)
            k = (y * W + x) * 3
            out[k] = min(255, max(0, r)) & 0xFC
            out[k + 1] = min(255, max(0, g)) & 0xFC
            out[k + 2] = min(255, max(0, b)) & 0xFC
    return out


def write_png(pixels, path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += pixels[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        c += struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def main():
    draw_scene()
    pixels = finish()
    outdir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'entry.png')
    write_png(pixels, path)
    print('wrote', path, os.path.getsize(path), 'bytes')


if __name__ == '__main__':
    main()
