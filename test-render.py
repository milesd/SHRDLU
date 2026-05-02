#!/usr/bin/env python3
"""
Isometric depth-ordering test.

Two cubes share a face at wy=400.  They overlap on screen.

  RED  -- wx 300-600, wy 100-400  (near: wx+wy center = 700)
  BLUE -- wx 300-600, wy 400-700  (far:  wx+wy center = 1000)

Correct result: RED appears in FRONT of BLUE.
If reversed: BLUE will appear in front of RED.

A WHITE reference cube sits isolated at (100,100,0) so you
can see the basic block shape in a corner with no occlusion.

Axes drawn from origin (50,50,0):
  X axis (right-front)  → orange
  Y axis (left-front)   → cyan
  Z axis (up)           → yellow
"""

import sys

PW, PH   = 1600, 1020
ISO_SX   = 0.35
ISO_SY   = 0.175
ISO_SZ   = 0.30
OX, OY   = 800, 1000   # origin at bottom-center

PALETTE = [
    ( 8,  8, 10),   #  0 background
    (20, 18, 15),   #  1 floor
    (100, 25, 25),  #  2 RED   top
    ( 75, 15, 15),  #  3 RED   front
    ( 55, 10, 10),  #  4 RED   right
    ( 25,100, 25),  #  5 GREEN top
    ( 15, 75, 15),  #  6 GREEN front
    ( 10, 55, 10),  #  7 GREEN right
    ( 25, 25,100),  #  8 BLUE  top
    ( 15, 15, 75),  #  9 BLUE  front
    ( 10, 10, 55),  # 10 BLUE  right
    ( 95, 95, 95),  # 11 WHITE top
    ( 70, 70, 70),  # 12 WHITE front
    ( 50, 50, 50),  # 13 WHITE right
    (100, 60,  0),  # 14 X axis (orange)
    (  0,100,100),  # 15 Y axis (cyan)
    (100,100,  0),  # 16 Z axis (yellow)
]

COLOR_IDX = {
    'RED':   (2,  3,  4),
    'GREEN': (5,  6,  7),
    'BLUE':  (8,  9, 10),
    'WHITE': (11, 12, 13),
}

# 5x7 bitmap font for X Y Z (each row is a bitmask, LSB = leftmost pixel)
GLYPHS = {
    'X': [0b10001, 0b01010, 0b00100, 0b01010, 0b10001],
    'Y': [0b10001, 0b01010, 0b00100, 0b00100, 0b00100],
    'Z': [0b11111, 0b11000, 0b01100, 0b00110, 0b11111],
}

def iso_pt(wx, wy, wz):
    x = round(OX + (wx - wy) * ISO_SX)
    y = round(OY - (wx + wy) * ISO_SY - wz * ISO_SZ)
    return (x, y)

def make_buf():
    return [[0] * PW for _ in range(PH)]

def pbuf_set(buf, x, y, ci):
    if 0 <= x < PW and 0 <= y < PH:
        buf[y][x] = ci

def draw_line(buf, x0, y0, x1, y1, ci):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        pbuf_set(buf, x0, y0, ci)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy; x0 += sx
        if e2 < dx:
            err += dx; y0 += sy

def draw_glyph(buf, ch, px, py, ci):
    rows = GLYPHS.get(ch)
    if not rows:
        return
    for row, bits in enumerate(rows):
        for col in range(5):
            if bits & (1 << col):
                pbuf_set(buf, px + col, py + row, ci)

def fill_poly(buf, pts, ci):
    if len(pts) < 3:
        return
    ys = [p[1] for p in pts]
    y1 = max(0, min(ys))
    y2 = min(PH - 1, max(ys))
    n = len(pts)
    for y in range(y1, y2 + 1):
        xs = []
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay <= y < by) or (by <= y < ay):
                frac = (y - ay) / (by - ay)
                xs.append(round(ax + frac * (bx - ax)))
        if len(xs) >= 2:
            for x in range(max(0, min(xs)), min(PW - 1, max(xs)) + 1):
                buf[y][x] = ci

def draw_block(buf, wx1, wy1, wz1, wx2, wy2, wz2, color):
    ci_t, ci_l, ci_r = COLOR_IDX[color]
    p000 = iso_pt(wx1, wy1, wz1)
    p100 = iso_pt(wx2, wy1, wz1)
    p010 = iso_pt(wx1, wy2, wz1)
    p001 = iso_pt(wx1, wy1, wz2)
    p101 = iso_pt(wx2, wy1, wz2)
    p011 = iso_pt(wx1, wy2, wz2)
    p111 = iso_pt(wx2, wy2, wz2)
    fill_poly(buf, [p000, p010, p011, p001], ci_l)   # left  face (x-min)
    fill_poly(buf, [p000, p100, p101, p001], ci_r)   # front face (y-min)
    fill_poly(buf, [p001, p101, p111, p011], ci_t)   # top   face (z-max)

def draw_pyramid(buf, wx1, wy1, wz1, wx2, wy2, wz2, color):
    ci_t, ci_l, ci_r = COLOR_IDX[color]
    wmx = (wx1 + wx2) / 2
    wmy = (wy1 + wy2) / 2
    p000 = iso_pt(wx1, wy1, wz1)
    p100 = iso_pt(wx2, wy1, wz1)
    p010 = iso_pt(wx1, wy2, wz1)
    apex = iso_pt(wmx, wmy, wz2)
    fill_poly(buf, [p000, p010, apex], ci_l)   # left  face (x-min)
    fill_poly(buf, [p000, p100, apex], ci_r)   # front face (y-min)

def draw_floor(buf):
    fill_poly(buf, [
        iso_pt(   0,    0, 0), iso_pt(1100,    0, 0),
        iso_pt(1100, 1100, 0), iso_pt(   0, 1100, 0),
    ], 1)

def draw_axes(buf):
    O  = (50, 50, 0)
    XE = (50, 550, 0)    # X: increasing wy direction (left-front)
    YE = (550, 50, 0)    # Y: increasing wx direction (right-front)
    ZE = (50, 50, 500)

    ox, oy = iso_pt(*O)
    xx, xy = iso_pt(*XE)
    yx, yy = iso_pt(*YE)
    zx, zy = iso_pt(*ZE)

    draw_line(buf, ox, oy, xx, xy, 14)   # X orange
    draw_line(buf, ox, oy, yx, yy, 15)   # Y cyan
    draw_line(buf, ox, oy, zx, zy, 16)   # Z yellow

    draw_glyph(buf, 'X', xx - 9, xy - 3, 14)
    draw_glyph(buf, 'Y', yx + 4, yy - 3, 15)
    draw_glyph(buf, 'Z', zx + 4, zy - 3, 16)

def emit_sixel(buf):
    ESC = '\x1b'
    out = sys.stdout
    out.write(f'{ESC}P0;0;0q')
    out.write(f'"1;1;{PW};{PH}')
    for i, (r, g, b) in enumerate(PALETTE):
        out.write(f'#{i};2;{r};{g};{b}')
    for band in range(PH // 6):
        y0 = band * 6
        used = sorted({buf[y0 + dy][x] for dy in range(6) for x in range(PW)})
        first = True
        for ci in used:
            if not first:
                out.write('$')
            first = False
            out.write(f'#{ci}')
            run_ch = run_len = None
            for x in range(PW):
                bits = sum((1 << dy) for dy in range(6) if buf[y0 + dy][x] == ci)
                ch = 63 + bits
                if ch == run_ch:
                    run_len += 1
                else:
                    if run_ch is not None:
                        out.write(f'!{run_len}{chr(run_ch)}' if run_len > 3
                                  else chr(run_ch) * run_len)
                    run_ch, run_len = ch, 1
            if run_ch is not None:
                out.write(f'!{run_len}{chr(run_ch)}' if run_len > 3
                          else chr(run_ch) * run_len)
        out.write('-')
    out.write(f'{ESC}\\')
    out.flush()

# (wx1, wy1, wz1, wx2, wy2, wz2, color, shape)
BLOCKS = [
    (100, 100, 0, 400, 400, 300, 'WHITE',  'block'),    # isolated reference
    (300, 100, 0, 600, 400, 300, 'RED',    'block'),    # near
    (300, 400, 0, 600, 700, 300, 'BLUE',   'block'),    # far
    (700, 100, 0, 1000, 400, 300, 'GREEN', 'pyramid'),  # pyramid, same depth as RED
]

buf = make_buf()
draw_floor(buf)

for b in sorted(BLOCKS, key=lambda b: b[0] + b[1], reverse=True):
    wx1, wy1, wz1, wx2, wy2, wz2, color, shape = b
    if shape == 'pyramid':
        draw_pyramid(buf, wx1, wy1, wz1, wx2, wy2, wz2, color)
    else:
        draw_block(buf, wx1, wy1, wz1, wx2, wy2, wz2, color)

draw_axes(buf)   # drawn last so labels are never occluded
emit_sixel(buf)
print()
print("Axes from origin (50,50,0):")
print("  X (orange) = increasing wy  →  left-front on screen")
print("  Y (cyan)   = increasing wx  →  right-front on screen")
print("  Z (yellow) = increasing wz  →  up")
print()
print("Expected: RED in FRONT of BLUE")
