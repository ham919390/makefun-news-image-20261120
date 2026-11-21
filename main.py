#!/usr/bin/env python3
"""
main.py -- draws entry.png: "THE DAILY ORBIT", a one-picture newspaper
front page summing up the world news of Friday 20 November 2026.

Pure Python standard library only (no Pillow, no network, no external
assets): a small rasterizer draws flat editorial-style panels -- masthead,
lead story, six smaller stories -- with a hand-built 5x7 bitmap font, and
writes a deterministic PNG with zlib.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   (writes out/entry.png)
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (250, 243, 222)       # cream newsprint
PAPER_DARK = (238, 228, 196)
INK = (20, 33, 61)            # ink navy
INK_LIGHT = (52, 74, 115)
RED = (193, 39, 45)           # accent red
WHITE = (255, 255, 255)
SKY = (214, 228, 240)
NIGHT = (18, 28, 52)
GREY = (120, 128, 140)
GOLD = (232, 176, 32)
GREEN = (46, 125, 87)
TAN = (222, 196, 150)
DARK = (30, 30, 34)

# ---------------------------------------------------------------- canvas
buf = bytearray(W * H * 3)


def fill_rect(x, y, w, h, c):
    """Fill an axis-aligned rectangle (clipped to the canvas)."""
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        off = (yy * W + x0) * 3
        buf[off:off + len(row)] = row


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        off = (y * W + x) * 3
        buf[off:off + 3] = bytes(c)


def line(x0, y0, x1, y1, c, width=1):
    """Bresenham line, thickened by stamping small squares."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    r = width // 2
    while True:
        fill_rect(x0 - r, y0 - r, width, width, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c, fill=True):
    if fill:
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5)
            fill_rect(cx - dx, yy, 2 * dx + 1, 1, c)
    else:
        for a in range(360):
            import math
            set_px(int(cx + r * math.cos(math.radians(a))),
                   int(cy + r * math.sin(math.radians(a))), c)


def ellipse(cx, cy, rx, ry, c):
    for yy in range(cy - ry, cy + ry + 1):
        t = 1.0 - ((yy - cy) / ry) ** 2
        if t < 0:
            continue
        dx = int(rx * t ** 0.5)
        fill_rect(cx - dx, yy, 2 * dx + 1, 1, c)


def poly_fill(points, c):
    """Scanline fill of a simple polygon (list of (x, y))."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    for yy in range(max(0, min(ys)), min(H, max(ys)) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= yy < y1) or (y1 <= yy < y0):
                t = (yy - y0) / (y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            fill_rect(int(xs[i]), yy, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)


def star(cx, cy, r_out, r_in, c, points=5, rot=-90):
    import math
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / points)
        pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    poly_fill(pts, c)


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, "1" = ink. Uppercase, digits and the
# punctuation the headlines use. Drawn at any integer scale.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "\u2022": ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
    "\u2014": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "\u00b0": ("01100", "10010", "10010", "01100", "00000", "00000", "00000"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, color):
    """Draw uppercase text at (x, y); returns the x just past the text."""
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row_i, row in enumerate(glyph):
            for col_i, bit in enumerate(row):
                if bit == "1":
                    fill_rect(cx + col_i * scale, y + row_i * scale,
                              scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(cx, y, s, scale, color):
    draw_text(cx - text_width(s, scale) // 2, y, s, scale, color)


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(x, y, s, scale, color, max_w, leading=None):
    """Draw a wrapped paragraph; returns the y just below it."""
    if leading is None:
        leading = 9 * scale
    yy = y
    for ln in wrap_text(s, scale, max_w):
        draw_text(x, yy, ln, scale, color)
        yy += leading
    return yy


# ---------------------------------------------------------------- PNG out
def _chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))


def write_png(path):
    raw = b"".join(b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3])
                   for y in range(H))
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
           + _chunk(b"IDAT", zlib.compress(raw, 9))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- layout
MARGIN = 24
CONTENT_W = W - 2 * MARGIN


def panel(x, y, w, h, bg=PAPER_DARK, border=INK):
    fill_rect(x, y, w, h, bg)
    fill_rect(x, y, w, 2, border)
    fill_rect(x, y + h - 2, w, 2, border)
    fill_rect(x, y, 2, h, border)
    fill_rect(x + w - 2, y, 2, h, border)


def masthead():
    fill_rect(0, 0, W, H, PAPER)
    # top rules
    fill_rect(MARGIN, 22, CONTENT_W, 4, INK)
    draw_text_centered(W // 2, 32, "THE DAILY ORBIT", 7, INK)
    draw_text_centered(W // 2, 90, "FRIDAY, 20 NOVEMBER 2026", 3, RED)
    draw_text_centered(W // 2, 114, "WORLD NEWS IN ONE PAGE", 2, INK_LIGHT)
    fill_rect(MARGIN, 138, CONTENT_W, 5, RED)
    fill_rect(MARGIN, 146, CONTENT_W, 2, INK)


def lead_art(x, y, w, h):
    """Night sky over Poland: missile trails, bursts, Polish flag."""
    fill_rect(x, y, w, h, NIGHT)
    # stars
    for sx, sy in [(30, 26), (90, 60), (150, 30), (210, 70), (260, 40),
                   (320, 24), (360, 64), (60, 110), (180, 96), (300, 110)]:
        fill_rect(x + sx, y + sy, 3, 3, WHITE)
    # ground
    fill_rect(x, y + h - 64, w, 64, (38, 52, 40))
    # Polish flag: white over red
    fill_rect(x + 24, y + h - 52, 110, 18, WHITE)
    fill_rect(x + 24, y + h - 34, 110, 18, RED)
    fill_rect(x + 24, y + h - 52, 110, 2, INK)
    fill_rect(x + 24, y + h - 52, 2, 36, INK)
    fill_rect(x + 132, y + h - 52, 2, 36, INK)
    fill_rect(x + 24, y + h - 16, 110, 2, INK)
    # missile trails (white-hot lines with red glow)
    line(x + 40, y + 30, x + 250, y + 210, RED, 5)
    line(x + 40, y + 30, x + 250, y + 210, WHITE, 2)
    line(x + 150, y + 18, x + 320, y + 190, RED, 5)
    line(x + 150, y + 18, x + 320, y + 190, WHITE, 2)
    # missile heads
    circle(x + 250, y + 210, 7, WHITE)
    circle(x + 320, y + 190, 7, WHITE)
    # explosion bursts at the impact points, on the ground line
    star(x + 250, y + 212, 30, 12, (255, 140, 40))
    star(x + 250, y + 212, 18, 7, (255, 220, 90))
    star(x + 320, y + 192, 24, 10, (255, 140, 40))
    star(x + 320, y + 192, 14, 6, (255, 220, 90))


def lead_story(y, h):
    panel(MARGIN, y, CONTENT_W, h, bg=PAPER_DARK)
    art_w = 400
    lead_art(MARGIN + 10, y + 10, art_w, h - 20)
    tx = MARGIN + 10 + art_w + 22
    tw = MARGIN + CONTENT_W - 10 - tx
    draw_text(tx, y + 24, "POLAND \u2022 NATO", 2, RED)
    yy = draw_para(tx, y + 52, "MISSILES FALL ON POLAND", 4, INK, tw)
    yy = draw_para(tx, yy + 10,
                   "TWO RUSSIAN MISSILES AND A SUSPECTED DRONE CAME "
                   "DOWN IN POLAND. WARSAW CALLS IT A DELIBERATE "
                   "PROVOCATION. NATO CALLS IT A GRAVE VIOLATION OF "
                   "ITS AIRSPACE.", 2, INK_LIGHT, tw)
    draw_text(tx, y + h - 28, "KYIV ALSO HIT IN OVERNIGHT STRIKES", 2, RED)


def story_panel(x, y, w, h, kicker, headline, caption, art):
    panel(x, y, w, h, bg=PAPER_DARK)
    art(x + 10, y + 10, w - 20, 94)
    ty = y + 114
    draw_text(x + 12, ty, kicker, 2, RED)
    ty = draw_para(x + 12, ty + 24, headline, 3, INK, w - 24)
    draw_para(x + 12, ty + 8, caption, 2, INK_LIGHT, w - 24)


def art_scales(x, y, w, h):
    """Scales of justice on pale blue."""
    fill_rect(x, y, w, h, SKY)
    cx, cy = x + w // 2, y + 20
    fill_rect(cx - 3, cy, 6, 56, INK)
    fill_rect(cx - 62, cy + 8, 124, 5, INK)
    circle(cx, cy, 6, GOLD)
    for dx in (-56, 56):
        line(cx + dx, cy + 10, cx + dx - 22, cy + 40, INK, 3)
        line(cx + dx, cy + 10, cx + dx + 22, cy + 40, INK, 3)
        poly_fill([(cx + dx - 26, cy + 40), (cx + dx + 26, cy + 40),
                   (cx + dx, cy + 58)], GOLD)
    fill_rect(cx - 34, cy + 58, 68, 7, INK)
    fill_rect(cx - 44, cy + 65, 88, 7, INK)


def art_markets(x, y, w, h):
    """Red plunging chart line."""
    fill_rect(x, y, w, h, WHITE)
    for gy in range(y + 14, y + h - 6, 18):
        fill_rect(x + 8, gy, w - 16, 1, (228, 232, 238))
    pts = [(x + 12, y + 16), (x + 60, y + 26), (x + 105, y + 22),
           (x + 150, y + 40), (x + 195, y + 36), (x + 240, y + 60),
           (x + w - 14, y + 74)]
    for a, b in zip(pts, pts[1:]):
        line(a[0], a[1], b[0], b[1], RED, 4)
    for px, py in pts:
        circle(px, py, 4, RED)
    # down arrow
    ax, ay = x + w - 52, y + 8
    poly_fill([(ax, ay + 26), (ax + 34, ay + 26), (ax + 17, ay + 44)], RED)
    fill_rect(ax + 12, ay, 10, 28, RED)


def art_summit(x, y, w, h):
    """Three flags: USA, China, Russia."""
    fill_rect(x, y, w, h, PAPER_DARK)
    fw, fh, gap = (w - 24) // 3, 56, 12
    # USA: stripes + blue canton
    ux = x + 12
    for i in range(7):
        fill_rect(ux, y + 8 + i * 8, fw, 8,
                  RED if i % 2 == 0 else WHITE)
    fill_rect(ux, y + 8, fw // 2, 32, (30, 60, 140))
    for sx in range(3):
        for sy in range(2):
            fill_rect(ux + 8 + sx * 16, y + 13 + sy * 13, 4, 4, WHITE)
    # China: red + gold stars
    cx = ux + fw + gap
    fill_rect(cx, y + 8, fw, fh, (222, 41, 16))
    star(cx + 24, y + 26, 12, 5, GOLD)
    star(cx + 52, y + 20, 6, 2, GOLD)
    star(cx + 62, y + 34, 6, 2, GOLD)
    star(cx + 52, y + 48, 6, 2, GOLD)
    # Russia: white / blue / red bands
    rx = cx + fw + gap
    fill_rect(rx, y + 8, fw, 19, WHITE)
    fill_rect(rx, y + 27, fw, 19, (0, 57, 166))
    fill_rect(rx, y + 46, fw, 18, (213, 0, 50))
    draw_text(x + 12, y + 74, "USA  •  CHINA  •  RUSSIA", 2, INK_LIGHT)


def art_eu_uk(x, y, w, h):
    """EU circle of stars beside a simplified Union Jack."""
    fill_rect(x, y, w, h, SKY)
    # EU flag
    ex = x + 16
    fill_rect(ex, y + 8, 120, 72, (0, 51, 153))
    import math
    for i in range(12):
        a = math.radians(i * 30 - 90)
        star(int(ex + 60 + 30 * math.cos(a)),
             int(y + 44 + 26 * math.sin(a)), 5, 2, GOLD)
    # Union Jack (simplified)
    ux = ex + 136
    fill_rect(ux, y + 8, 120, 72, (1, 33, 105))
    line(ux, y + 8, ux + 120, y + 80, WHITE, 10)
    line(ux + 120, y + 8, ux, y + 80, WHITE, 10)
    fill_rect(ux + 54, y + 8, 12, 72, WHITE)
    fill_rect(ux, y + 38, 120, 12, WHITE)
    fill_rect(ux + 57, y + 8, 6, 72, RED)
    fill_rect(ux, y + 41, 120, 6, RED)


def art_quake(x, y, w, h):
    """Seismograph trace over cracked ground."""
    fill_rect(x, y, w, h, TAN)
    line(x + 8, y + 36, x + 60, y + 36, INK, 3)
    line(x + 60, y + 36, x + 78, y + 14, INK, 3)
    line(x + 78, y + 14, x + 96, y + 62, INK, 3)
    line(x + 96, y + 62, x + 114, y + 24, INK, 3)
    line(x + 114, y + 24, x + 132, y + 56, INK, 3)
    line(x + 132, y + 56, x + 150, y + 36, INK, 3)
    line(x + 150, y + 36, x + 168, y + 18, INK, 3)
    line(x + 168, y + 18, x + 186, y + 50, INK, 3)
    line(x + 186, y + 50, x + 210, y + 36, INK, 3)
    line(x + 210, y + 36, x + w - 8, y + 36, INK, 3)
    # cracked ground
    fill_rect(x, y + 70, w, h - 70, (120, 96, 66))
    line(x + 30, y + 70, x + 60, y + h - 6, (60, 48, 32), 3)
    line(x + 60, y + h - 6, x + 90, y + 80, (60, 48, 32), 3)
    line(x + 180, y + 70, x + 200, y + h - 6, (60, 48, 32), 3)


def art_gta(x, y, w, h):
    """Gold record figure on dark green."""
    fill_rect(x, y, w, h, (16, 46, 32))
    draw_text_centered(x + w // 2, y + 12, "$2.3BN", 5, GOLD)
    draw_text_centered(x + w // 2, y + 56, "RECORD LAUNCH", 2, WHITE)
    # gold bars rising
    for i, bh in enumerate((6, 9, 12, 15)):
        fill_rect(x + 40 + i * 56, y + h - 4 - bh, 34, bh, GOLD)


def footer(y):
    fill_rect(MARGIN, y, CONTENT_W, 2, INK)
    draw_text_centered(W // 2, y + 12,
                       "S&P 500 -3.7%  \u2022  NIKKEI -5.06%  \u2022  "
                       "FTSE 100 -1.02%  \u2022  BRENT $89.87", 2, INK_LIGHT)


def main():
    masthead()
    lead_story(158, 280)
    row1_y, row_h = 454, 250
    gap = 16
    pw = (CONTENT_W - 2 * gap) // 3
    stories1 = [
        ("THE HAGUE \u2022 JUSTICE",
         "MYANMAR GUILTY OF GENOCIDE",
         "ICJ: GENOCIDE AGAINST THE ROHINGYA.",
         art_scales),
        ("MARKETS",
         "STOCKS PLUNGE IN AI SELL-OFF",
         "S&P 500 -3.7%. NIKKEI -5.06%.",
         art_markets),
        ("SHENZHEN \u2022 SUMMIT",
         "TRUMP, XI, PUTIN SIGN PACT",
         "JOINT DECLARATION. NO UKRAINE, NO IRAN.",
         art_summit),
    ]
    for i, (kicker, headline, caption, art) in enumerate(stories1):
        story_panel(MARGIN + i * (pw + gap), row1_y, pw, row_h,
                    kicker, headline, caption, art)
    row2_y = row1_y + row_h + gap
    stories2 = [
        ("BRUSSELS \u2022 EUROPE",
         "BRITAIN AND EU SEAL RESET DEAL",
         "FOOD TRADE, CARBON AND YOUTH MOBILITY.",
         art_eu_uk),
        ("PERU \u2022 DISASTER",
         "6.7 QUAKE SHAKES CENTRAL PERU",
         "STRONG QUAKE HITS CERRO DE PASCO.",
         art_quake),
        ("CULTURE \u2022 RECORDS",
         "GTA 6 SALES TOP $2.3BN",
         "RECORD-BREAKING LAUNCH WEEK.",
         art_gta),
    ]
    for i, (kicker, headline, caption, art) in enumerate(stories2):
        story_panel(MARGIN + i * (pw + gap), row2_y, pw, row_h,
                    kicker, headline, caption, art)
    footer(row2_y + row_h + 12)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    size = write_png(os.path.join(out_dir, "entry.png"))
    print(f"wrote {os.path.join(out_dir, 'entry.png')} ({size} bytes)")


if __name__ == "__main__":
    main()
