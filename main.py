#!/usr/bin/env python3
"""The Catalogue Photo of an Impossible Gadget.

Writes one 1024x1024 PNG catalogue photograph to /output/entry.png
(or ./entry.png when /output is not writable): a studio product shot of
FROSTBOIL, the electric kettle that boils ice -- it pours a stream of ice
cubes into a mug, its one accessory. Pure standard library: the picture is
rendered pixel by pixel and encoded as PNG with zlib.
"""
import math
import os
import struct
import sys
import zlib

W, H = 1024, 1024


def clamp(v, lo=0, hi=255):
    return lo if v < lo else hi if v > hi else v


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)

    def set(self, x, y, rgb, a=1.0):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            if a >= 1.0:
                self.px[i], self.px[i + 1], self.px[i + 2] = rgb
            else:
                for c in range(3):
                    self.px[i + c] = clamp(
                        int(self.px[i + c] * (1 - a) + rgb[c] * a))

    def rect(self, x0, y0, x1, y1, rgb, a=1.0):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.set(x, y, rgb, a)

    def circle(self, cx, cy, r, rgb, a=1.0):
        r2 = r * r
        for y in range(max(0, cy - r), min(self.h, cy + r + 1)):
            dy = y - cy
            dx = int(math.sqrt(max(0, r2 - dy * dy)))
            for x in range(max(0, cx - dx), min(self.w, cx + dx + 1)):
                self.set(x, y, rgb, a)

    def ellipse(self, cx, cy, rx, ry, rgb, a=1.0):
        for y in range(max(0, cy - ry), min(self.h, cy + ry + 1)):
            dy = (y - cy) / max(1, ry)
            dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
            for x in range(max(0, cx - dx), min(self.w, cx + dx + 1)):
                self.set(x, y, rgb, a)

    def line(self, x0, y0, x1, y1, thick, rgb, a=1.0):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            self.circle(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t),
                        thick // 2, rgb, a)

    def poly(self, pts, rgb, a=1.0):
        ys = sorted(set(p[1] for p in pts))
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if y0 == y1:
                    continue
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(max(0, int(xs[j])), min(self.w, int(xs[j + 1]) + 1)):
                    self.set(x, y, rgb, a)

    def rrect(self, x0, y0, x1, y1, r, rgb, a=1.0):
        self.rect(x0 + r, y0, x1 - r, y1, rgb, a)
        self.rect(x0, y0 + r, x1, y1 - r, rgb, a)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.circle(cx, cy, r, rgb, a)


def vgrad(c, y0, y1, top, bot):
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        rgb = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
        c.rect(0, y, W - 1, y, rgb)


def soft_shadow(c, cx, cy, rx, ry, dark=(62, 52, 36)):
    for k, a in ((1.0, 0.10), (0.8, 0.08), (0.6, 0.06)):
        c.ellipse(cx, cy, int(rx * k), int(ry * k), dark, a)


def ice_cube(c, cx, cy, s, rot):
    cs, sn = math.cos(rot), math.sin(rot)
    h = s / 2
    pts = []
    for dx, dy in ((-h, -h), (h, -h), (h, h), (-h, h)):
        pts.append((int(cx + dx * cs - dy * sn), int(cy + dx * sn + dy * cs)))
    c.poly(pts, (214, 236, 247))
    # bright top edge, shaded right edge
    c.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], 3, (255, 255, 255))
    c.line(pts[1][0], pts[1][1], pts[2][0], pts[2][1], 3, (168, 208, 232))
    c.line(pts[2][0], pts[2][1], pts[3][0], pts[3][1], 3, (168, 208, 232))


def draw():
    c = Canvas(W, H)
    # --- studio backdrop: soft vertical gradient + glow ---
    vgrad(c, 0, H - 1, (245, 242, 236), (220, 213, 199))
    for r, a in ((520, 0.10), (380, 0.10), (240, 0.10)):
        c.circle(512, 330, r, (255, 255, 252), a)
    # floor band
    c.rect(0, 830, W - 1, H - 1, (206, 198, 183))
    c.line(0, 830, W - 1, 830, 2, (196, 187, 170))
    soft_shadow(c, 420, 836, 250, 26)
    soft_shadow(c, 720, 836, 115, 18)

    # --- kettle handle (behind body) ---
    for p0, p1 in (((282, 490), (232, 505)), ((232, 505), (216, 570)),
                   ((216, 570), (232, 640)), ((232, 640), (282, 652))):
        c.line(p0[0], p0[1], p1[0], p1[1], 24, (15, 56, 74))

    # --- kettle body ---
    c.rrect(280, 380, 560, 800, 46, (27, 85, 110))
    c.rrect(280, 380, 560, 800, 46, (18, 58, 76), a=0.0)  # keep shape crisp
    # right-side shade + left highlight
    c.rrect(500, 396, 544, 784, 30, (13, 48, 64), a=0.55)
    c.rrect(300, 400, 332, 780, 22, (64, 142, 168), a=0.75)
    c.line(296, 410, 296, 770, 3, (150, 205, 224), a=0.8)
    # lid + brass knob
    c.ellipse(420, 378, 148, 26, (18, 56, 74))
    c.ellipse(420, 374, 148, 22, (30, 92, 118))
    c.circle(420, 348, 17, (200, 162, 74))
    c.circle(415, 343, 6, (232, 200, 120))
    # base band + feet
    c.rrect(280, 762, 560, 800, 30, (13, 48, 64))
    c.rect(310, 800, 340, 814, (13, 48, 64))
    c.rect(500, 800, 530, 814, (13, 48, 64))
    # cream label (text-free, belongs to the product)
    c.rrect(348, 560, 492, 662, 12, (243, 233, 210))
    c.rrect(348, 560, 492, 662, 12, (27, 85, 110), a=0.0)
    c.line(348, 560, 492, 560, 3, (27, 85, 110))
    c.line(348, 662, 492, 662, 3, (27, 85, 110))
    c.circle(420, 611, 26, (27, 85, 110))
    c.circle(420, 611, 14, (243, 233, 210))

    # --- spout (pours up-right) ---
    c.poly([(540, 480), (598, 432), (656, 392), (640, 372),
            (584, 408), (528, 446)], (27, 85, 110))
    c.poly([(540, 480), (598, 432), (656, 392), (640, 372),
            (584, 408), (528, 446)], (13, 48, 64), a=0.0)
    c.line(548, 468, 636, 392, 4, (64, 142, 168), a=0.7)

    # --- stream of ice cubes, spout tip -> mug ---
    cubes = [(655, 400, 42, 0.3), (668, 452, 36, -0.4), (682, 500, 44, 0.2),
             (694, 548, 34, 0.6), (706, 592, 42, -0.2), (714, 634, 36, 0.4),
             (718, 668, 30, -0.5)]
    for cx, cy, s, rot in cubes:
        ice_cube(c, cx, cy, s, rot)
    # tiny droplets
    for cx, cy, r in ((660, 430, 5), (700, 570, 4), (712, 616, 5)):
        c.circle(cx, cy, r, (214, 236, 247))

    # --- cold wisps above the mug ---
    for cx, cy, r in ((688, 648, 15), (726, 626, 19), (758, 652, 13)):
        c.circle(cx, cy, r, (226, 240, 248), 0.45)

    # --- mug: the one accessory ---
    c.rrect(640, 690, 800, 830, 18, (251, 250, 247))
    c.rrect(640, 690, 800, 830, 18, (232, 228, 219), a=0.0)
    c.ellipse(720, 690, 80, 20, (223, 219, 210))
    c.ellipse(720, 690, 68, 15, (207, 221, 230))
    ice_cube(c, 700, 688, 22, 0.3)
    ice_cube(c, 736, 690, 20, -0.4)
    # mug handle
    for p0, p1 in (((800, 716), (846, 730)), ((846, 730), (846, 786)),
                   ((846, 786), (800, 796))):
        c.line(p0[0], p0[1], p1[0], p1[1], 16, (216, 211, 200))
    for p0, p1 in (((800, 716), (846, 730)), ((846, 730), (846, 786)),
                   ((846, 786), (800, 796))):
        c.line(p0[0], p0[1], p1[0], p1[1], 10, (251, 250, 247))
    # mug base shade
    c.rrect(640, 806, 800, 830, 14, (228, 223, 212), a=0.5)
    return c


def write_png(c, path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw.extend(c.px[y * stride:(y + 1) * stride])
    data = zlib.compress(bytes(raw), 9)

    def chunk(typ, payload):
        out = struct.pack(">I", len(payload)) + typ + payload
        out += struct.pack(">I", zlib.crc32(typ + payload) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", data)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "ENTRY_PATH", "/output/entry.png")
    canvas = draw()
    try:
        size = write_png(canvas, path)
    except OSError:
        path = "entry.png"
        size = write_png(canvas, path)
    print(f"wrote {path}: {W}x{H}, {size} bytes")


if __name__ == "__main__":
    main()
