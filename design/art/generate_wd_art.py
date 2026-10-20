#!/usr/bin/env python3
"""Deterministic generator for the WD Display mark and all shipped Android artwork.

Everything here is original geometry defined by the numbers in this file. No
third-party or Apple artwork, logo or font file is copied or embedded; the mark
and the wordmark are drawn from the polygon math below. Outputs are a pure
function of these constants, so re-running rewrites byte-identical PNGs on any
machine with a Python 3 standard library (zlib only, no Pillow).

Shipped outputs (paths relative to the repository root):
  app/src/main/res/mipmap-mdpi/ic_launcher.png            48
  app/src/main/res/mipmap-hdpi/ic_launcher.png            72
  app/src/main/res/mipmap-xhdpi/ic_launcher.png           96
  app/src/main/res/mipmap-xxhdpi/ic_launcher.png          144
  app/src/main/res/mipmap-xxxhdpi/ic_launcher.png         192
  app/src/main/res/drawable-xxxhdpi/ic_launcher_foreground.png   432
  app/src/main/res/drawable-xxxhdpi/ic_launcher_background.png   432
  app/src/main/res/drawable-xxxhdpi/ic_launcher_monochrome.png   432
  app/src/main/res/drawable/tv_banner.png                  320x180
  app/src/main/res/drawable-xhdpi/tv_banner.png            640x360
  app/src/main/res/drawable/ic_wd_monochrome.xml           vector, 24dp
Also writes design/art/wd-mark.svg (master geometry, documentation only).

Usage:  python3 design/art/generate_wd_art.py
"""

import math
import os
import struct
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES = os.path.join(ROOT, "app", "src", "main", "res")
ART = os.path.join(ROOT, "design", "art")

# ---------------------------------------------------------------------------
# Mark geometry constants (design units; y grows downward)
# ---------------------------------------------------------------------------
# A geometric W is two mirrored right-angle strokes. Stroke A descends from the
# left tip to a bottom vertex and turns up to the middle peak; stroke B is its
# mirror about the vertical axis. Both are wide ribbons (uniform thickness) with
# flat-cut ends and a chamfered corner where the offset would spike.
MARK_W = 132.0          # tip to tip, pre-shear
MARK_H = 96.0           # tip line to bottom vertex
MARK_T = 25.0           # ribbon thickness (26% of height: legible at 48 px)
MARK_SEAM = 2.6         # gap where the two strokes meet at the middle peak
MARK_SHEAR = 0.20       # italic lean (x += shear * (MARK_H - y))
MARK_MITRE = 1.35       # mitre clamp as a multiple of half the thickness

# Adaptive-icon safe zone: key content stays inside 66dp of the 108dp canvas.
ADAPTIVE = 432          # 108dp at xxxhdpi
SAFE = 264              # 66dp at xxxhdpi
LEGACY_MARK_FRACTION = 0.66   # glyph width as a fraction of a legacy icon tile

# ---------------------------------------------------------------------------
# Palette (mirrors the Compose tokens in WdTheme.kt)
# ---------------------------------------------------------------------------
TILE_TOP = (0x2A, 0x2A, 0x2F)
TILE_BOTTOM = (0x15, 0x15, 0x19)
TILE_RING = (0xFF, 0xFF, 0xFF)
SHEEN = (0xFF, 0xFF, 0xFF)
GLASS_TOP = (0xF7, 0xFF, 0xFD)
GLASS_MID = (0xC4, 0xEA, 0xE1)
GLASS_BOTTOM = (0x9D, 0xC7, 0xBF)
GLASS_SPEC = (0xFF, 0xFF, 0xFF)
GLASS_DEEP = (0x82, 0xAC, 0xA5)
SHADOW = (0x00, 0x00, 0x00)
WORDMARK_STRONG = ((0xF8, 0xF9, 0xFB), (0xCF, 0xD0, 0xD8))
WORDMARK_WEAK = ((0xE4, 0xE5, 0xEA), (0xB6, 0xB7, 0xBF))
# Ordered 4x4 Bayer matrix; a fraction of an LSB of dither removes the banding
# that an 8-bit vertical gradient shows across a tall dark tile.
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
DITHER = 1.6


# ---------------------------------------------------------------------------
# PNG writer
# ---------------------------------------------------------------------------
def write_png(path, w, h, rgba, include_alpha=True):
    colour_type = 6 if include_alpha else 2
    channels = 4 if include_alpha else 3
    raw = bytearray()
    stride = w * channels
    for y in range(h):
        raw.append(0)
        row = rgba[y * w * 4:(y + 1) * w * 4]
        if include_alpha:
            raw += row
        else:
            for x in range(w):
                if row[x * 4 + 3] != 255:
                    raise ValueError("opaque PNG requested but pixel %d,%d is not opaque"
                                     % (x, y))
                raw += row[x * 4:x * 4 + 3]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", w, h, 8, colour_type, 0, 0, 0)
    blob = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(blob)
    return len(blob)


# ---------------------------------------------------------------------------
# Vector helpers
# ---------------------------------------------------------------------------
def unit(vec):
    length = math.hypot(vec[0], vec[1])
    if length == 0:
        return (0.0, 0.0)
    return (vec[0] / length, vec[1] / length)


def bbox(polys):
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def shear_polys(polys, k, pivot_y):
    return [[(x + k * (pivot_y - y), y) for (x, y) in poly] for poly in polys]


def fit_polys(polys, bx, by, bw, bh):
    """Uniformly scale polys to fit inside the box (preserving aspect) and centre."""
    x0, y0, x1, y1 = bbox(polys)
    pw, ph = max(1e-9, x1 - x0), max(1e-9, y1 - y0)
    scale = min(bw / pw, bh / ph)
    tx = bx + (bw - pw * scale) / 2 - x0 * scale
    ty = by + (bh - ph * scale) / 2 - y0 * scale
    return [[(x * scale + tx, y * scale + ty) for (x, y) in poly] for poly in polys]


def scale_polys(polys, scale):
    return [[(x * scale, y * scale) for (x, y) in poly] for poly in polys]


def translate_polys(polys, dx, dy):
    return [[(x + dx, y + dy) for (x, y) in poly] for poly in polys]


def line_inter(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-12:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def offset_stroke(points, width, mitre_limit=1.6):
    """Closed outline polygon of a polyline stroked with `width`, flat caps.

    Joins take the exact intersection of the two offset edges. Only the convex
    side of a turn is chamfered, and only when the mitre would reach past
    mitre_limit * half the width; the concave side is always exact, so the notch
    of a sharp V stays crisp instead of being cut back.
    """
    half = width / 2.0
    count = len(points)
    if count < 2:
        return []
    segs = []
    for index in range(count - 1):
        p = points[index]
        q = points[index + 1]
        direction = unit((q[0] - p[0], q[1] - p[1]))
        segs.append((p, q, direction, (-direction[1], direction[0])))

    def edge(index, sign):
        """The two endpoints of one offset edge, from p to q."""
        p, q, _, normal = segs[index]
        return ((p[0] + sign * half * normal[0], p[1] + sign * half * normal[1]),
                (q[0] + sign * half * normal[0], q[1] + sign * half * normal[1]))

    def convex_sign(index):
        """Which side of the join at points[index] is the outside of the turn."""
        before = segs[index - 1][2]
        after = segs[index][2]
        cross = before[0] * after[1] - before[1] * after[0]
        return 1.0 if cross < 0 else -1.0

    def joins(sign):
        """Boundary points for every interior vertex, walking forwards."""
        result = []
        for index in range(1, count - 1):
            vertex = points[index]
            a = edge(index - 1, sign)
            b = edge(index, sign)
            hit = line_inter(a[0], a[1], b[0], b[1])
            if hit is None:
                result.extend([a[1], b[0]])
                continue
            reach = math.hypot(hit[0] - vertex[0], hit[1] - vertex[1])
            if sign != convex_sign(index) or reach <= mitre_limit * half:
                result.append(hit)
                continue
            bisector = unit((hit[0] - vertex[0], hit[1] - vertex[1]))
            centre = (vertex[0] + bisector[0] * mitre_limit * half,
                      vertex[1] + bisector[1] * mitre_limit * half)
            cut = (-bisector[1], bisector[0])
            near = (centre[0] - cut[0] * half * 8, centre[1] - cut[1] * half * 8)
            far = (centre[0] + cut[0] * half * 8, centre[1] + cut[1] * half * 8)
            first = line_inter(a[0], a[1], near, far) or a[1]
            second = line_inter(b[0], b[1], near, far) or b[0]
            result.extend([first, second])
        return result

    outline = [edge(0, 1.0)[0]]
    outline.extend(joins(1.0))
    outline.append(edge(count - 2, 1.0)[1])
    outline.append(edge(count - 2, -1.0)[1])
    outline.extend(reversed(joins(-1.0)))
    outline.append(edge(0, -1.0)[0])
    return outline


def disc(cx, cy, radius, segments=72):
    return [(cx + radius * math.cos(2 * math.pi * i / segments),
             cy + radius * math.sin(2 * math.pi * i / segments))
            for i in range(segments)]


def ring(cx, cy, radius, width, start_deg=0.0, end_deg=360.0, segments=None):
    """Annulus band polygon. A full turn produces a closed ring."""
    half = width / 2.0
    sweep = end_deg - start_deg
    if segments is None:
        segments = max(16, int(abs(sweep) / 6.0) + 2)
    outer, inner = [], []
    for step in range(segments + 1):
        angle = math.radians(start_deg + sweep * step / segments)
        co, si = math.cos(angle), math.sin(angle)
        outer.append((cx + (radius + half) * co, cy + (radius + half) * si))
        inner.append((cx + (radius - half) * co, cy + (radius - half) * si))
    return outer + list(reversed(inner))


def round_rect(x0, y0, x1, y1, radius, segments=12):
    radius = min(radius, (x1 - x0) / 2, (y1 - y0) / 2)
    pts = []
    corners = ((x0 + radius, y0 + radius, 180.0, 270.0),
               (x1 - radius, y0 + radius, 270.0, 360.0),
               (x1 - radius, y1 - radius, 0.0, 90.0),
               (x0 + radius, y1 - radius, 90.0, 180.0))
    for cx, cy, a0, a1 in corners:
        for step in range(segments + 1):
            angle = math.radians(a0 + (a1 - a0) * step / segments)
            pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return pts


def catmull_rom(anchors, samples_per_span=10):
    pts = []
    padded = [anchors[0]] + list(anchors) + [anchors[-1]]
    for index in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[index - 1], padded[index], padded[index + 1], padded[index + 2]
        for step in range(samples_per_span):
            t = step / samples_per_span
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            pts.append((x, y))
    pts.append(anchors[-1])
    return pts


# ---------------------------------------------------------------------------
# Rasteriser: 4x supersampled scanline coverage, box filtered to output size
# ---------------------------------------------------------------------------
SS = 4


def coverage(polys, w, h):
    """Union coverage mask, one byte per output pixel (0..255)."""
    big_w, big_h = w * SS, h * SS
    mask = bytearray(big_w * big_h)
    for poly in polys:
        pts = [(p[0] * SS, p[1] * SS) for p in poly]
        if len(pts) < 3:
            continue
        ys = [p[1] for p in pts]
        top = max(0, int(math.floor(min(ys))))
        bottom = min(big_h - 1, int(math.ceil(max(ys))))
        edges = []
        for index in range(len(pts)):
            x1, y1 = pts[index]
            x2, y2 = pts[(index + 1) % len(pts)]
            if y1 != y2:
                edges.append((x1, y1, x2, y2))
        for y in range(top, bottom + 1):
            scan = y + 0.5
            hits = []
            for x1, y1, x2, y2 in edges:
                if (y1 <= scan < y2) or (y2 <= scan < y1):
                    hits.append(x1 + (scan - y1) / (y2 - y1) * (x2 - x1))
            if len(hits) < 2:
                continue
            hits.sort()
            row = y * big_w
            for index in range(0, len(hits) - 1, 2):
                left = max(0, int(math.ceil(hits[index] - 0.5)))
                right = min(big_w, int(math.ceil(hits[index + 1] - 0.5)))
                if right <= left:
                    left = max(0, min(big_w - 1, int(hits[index])))
                    right = left + 1
                if right > left:
                    mask[row + left:row + right] = b"\x01" * (right - left)

    out = bytearray(w * h)
    for oy in range(h):
        base = oy * SS * big_w
        acc = mask[base:base + big_w]
        for k in range(1, SS):
            row = mask[base + k * big_w:base + k * big_w + big_w]
            acc = bytes(map(sum, zip(acc, row)))
        cov = bytes(a + b + c + d for a, b, c, d in
                    zip(acc[0::SS], acc[1::SS], acc[2::SS], acc[3::SS]))
        out[oy * w:(oy + 1) * w] = cov.translate(_SCALE16)
    return out


_SCALE16 = bytes(min(255, value * 255 // (SS * SS)) for value in range(256))


def mask_and(first, second):
    return bytes(min(a, b) for a, b in zip(first, second))


def mask_scale(mask, factor):
    if factor >= 1.0:
        return mask
    return bytes(int(v * factor) for v in mask)


def mask_shift(mask, w, h, dx, dy):
    out = bytearray(w * h)
    for y in range(h):
        source = y - dy
        if source < 0 or source >= h:
            continue
        row = mask[source * w:(source + 1) * w]
        for x in range(w):
            sx = x - dx
            if 0 <= sx < w:
                out[y * w + x] = row[sx]
    return bytes(out)


def mask_blur(mask, w, h, radius, passes=2):
    """Separable box blur; good enough for a soft icon drop shadow."""
    r = int(radius)
    if r < 1:
        return mask
    window = 2 * r + 1
    current = mask
    for _ in range(passes):
        horizontal = bytearray(w * h)
        for y in range(h):
            row = current[y * w:(y + 1) * w]
            total = sum(row[:r + 1])
            for x in range(w):
                horizontal[y * w + x] = total // window
                add = row[x + r + 1] if x + r + 1 < w else 0
                drop = row[x - r] if x - r >= 0 else 0
                total += add - drop
        vertical = bytearray(w * h)
        for x in range(w):
            total = 0
            for y in range(r + 1):
                total += horizontal[y * w + x]
            for y in range(h):
                vertical[y * w + x] = total // window
                add = horizontal[(y + r + 1) * w + x] if y + r + 1 < h else 0
                drop = horizontal[(y - r) * w + x] if y - r >= 0 else 0
                total += add - drop
        current = bytes(vertical)
    return current


def radial_mask(w, h, cx, cy, rx, ry, strength, falloff=1.9):
    out = bytearray(w * h)
    peak = int(255 * strength)
    for y in range(h):
        dy = (y + 0.5 - cy) / ry
        if abs(dy) >= 1.0:
            continue
        row = y * w
        for x in range(w):
            dx = (x + 0.5 - cx) / rx
            d2 = dx * dx + dy * dy
            if d2 >= 1.0:
                continue
            out[row + x] = int(peak * (1.0 - d2) ** falloff)
    return bytes(out)


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg=(0, 0, 0, 0)):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 4)
        if bg[3]:
            self.fill(bg)

    def fill(self, color):
        self.buf[:] = bytes(color) * (self.w * self.h)

    def fill_rows(self, color_fn):
        w, h = self.w, self.h
        for y in range(h):
            rgba = bytes(color_fn(y))
            if rgba[3] == 0:
                continue
            self.buf[y * w * 4:(y + 1) * w * 4] = rgba * w

    def blit(self, mask, color_fn, region=None):
        """Source-over blend of a coverage mask with per-pixel RGBA colour."""
        w, h, buf = self.w, self.h, self.buf
        x0, y0, x1, y1 = region or (0, 0, w, h)
        for y in range(max(0, y0), min(h, y1)):
            base = y * w * 4
            row = y * w
            for x in range(max(0, x0), min(w, x1)):
                coverage_byte = mask[row + x]
                if coverage_byte == 0:
                    continue
                red, green, blue, alpha = color_fn(x, y)
                if alpha <= 0:
                    continue
                src_a = coverage_byte / 255.0 * alpha
                if src_a <= 0:
                    continue
                index = base + x * 4
                dst_a = buf[index + 3] / 255.0
                out_a = src_a + dst_a * (1 - src_a)
                if out_a <= 0:
                    continue
                keep = dst_a * (1 - src_a) / out_a
                take = src_a / out_a
                buf[index] = int(red * take + buf[index] * keep + 0.5)
                buf[index + 1] = int(green * take + buf[index + 1] * keep + 0.5)
                buf[index + 2] = int(blue * take + buf[index + 2] * keep + 0.5)
                buf[index + 3] = int(out_a * 255 + 0.5)

    def is_opaque(self):
        return all(self.buf[index] == 255 for index in range(3, len(self.buf), 4))

    def save(self, path, include_alpha=None):
        if include_alpha is None:
            include_alpha = not self.is_opaque()
        return write_png(path, self.w, self.h, self.buf, include_alpha=include_alpha)


def mix(first, second, t):
    return tuple(int(a + (b - a) * t + 0.5) for a, b in zip(first, second))


def tile_colour(x, y, w, h, sheen_strength):
    """Dark neutral tile: vertical gradient plus one soft sheen, dithered."""
    base = mix(TILE_TOP, TILE_BOTTOM, y / max(1, h - 1))
    dx = (x + 0.5 - w * 0.5) / (w * 0.72)
    dy = (y + 0.5 - h * 0.34) / (h * 0.62)
    d2 = dx * dx + dy * dy
    lift = sheen_strength * (1.0 - d2) ** 1.9 if d2 < 1.0 else 0.0
    noise = (BAYER[y & 3][x & 3] / 16.0 - 0.5) * 2.0 * DITHER
    return (min(255, max(0, int(base[0] + (255 - base[0]) * lift + noise + 0.5))),
            min(255, max(0, int(base[1] + (255 - base[1]) * lift + noise + 0.5))),
            min(255, max(0, int(base[2] + (255 - base[2]) * lift + noise + 0.5))),
            1.0)


def paint_tile(canvas, w, h, mask=None, sheen_strength=0.11):
    area = mask if mask is not None else b"\xff" * (w * h)
    canvas.blit(area, lambda x, y: tile_colour(x, y, w, h, sheen_strength))


# ---------------------------------------------------------------------------
# The mark
# ---------------------------------------------------------------------------
def mark_design():
    """The two mirrored right-angle strokes in design units, drawn as polygons."""
    tip_left = (0.0, 0.0)
    bottom = (MARK_W / 4.0, MARK_H)
    peak = (MARK_W / 2.0, 0.0)
    direction = unit((peak[0] - bottom[0], peak[1] - bottom[1]))
    trimmed_peak = (peak[0] - direction[0] * MARK_SEAM, peak[1] - direction[1] * MARK_SEAM)
    left_skeleton = [tip_left, bottom, trimmed_peak]
    right_skeleton = [(MARK_W - x, y) for (x, y) in left_skeleton]
    left = offset_stroke(left_skeleton, MARK_T, MARK_MITRE)
    right = offset_stroke(right_skeleton, MARK_T, MARK_MITRE)
    return [left, right]


def mark_aspect():
    """Width/height ratio of the sheared mark, plus its design height."""
    x0, y0, x1, y1 = bbox(shear_polys(mark_design(), MARK_SHEAR, MARK_H))
    return (x1 - x0) / (y1 - y0), (y1 - y0)


def mark_fitted(bx, by, bw, bh):
    """Mark polygons fitted (uniform, centred) into the given box."""
    polys = shear_polys(mark_design(), MARK_SHEAR, MARK_H)
    return fit_polys(polys, bx, by, bw, bh)


def spans_by_column(mask, w, h):
    spans = [[] for _ in range(w)]
    for x in range(w):
        column = spans[x]
        y = 0
        while y < h:
            if mask[y * w + x] > 0:
                start = y
                while y < h and mask[y * w + x] > 0:
                    y += 1
                column.append((start, y - 1))
            else:
                y += 1
    return spans


def shade_glass(canvas, mask, w, h, mark_height):
    """Specular top rim, soft inner shading and a slight left-to-right falloff.

    Painted with source-over blending so the glass layers over an opaque tile
    instead of punching a semi-transparent hole in it.
    """
    rim = max(1.0, 0.055 * mark_height)
    foot = max(1.0, 0.024 * mark_height)
    spans = spans_by_column(mask, w, h)
    painted = {}
    for x in range(w):
        depth = 1.0 - 0.06 * (x / max(1, w - 1))
        for (top, bottom) in spans[x]:
            height = max(1.0, float(bottom - top))
            for y in range(top, bottom + 1):
                u = (y - top) / height
                if u < 0.5:
                    color = mix(GLASS_TOP, GLASS_MID, u / 0.5)
                else:
                    color = mix(GLASS_MID, GLASS_BOTTOM, (u - 0.5) / 0.5)
                rim_distance = y - top
                if rim_distance < rim:
                    color = mix(color, GLASS_SPEC, (1.0 - rim_distance / rim) ** 1.5 * 0.85)
                foot_distance = bottom - y
                if foot_distance < foot:
                    color = mix(color, GLASS_DEEP, (1.0 - foot_distance / foot) * 0.5)
                painted[y * w + x] = (int(color[0] * depth + 0.5),
                                      int(color[1] * depth + 0.5),
                                      int(color[2] * depth + 0.5))
    canvas.blit(mask, lambda x, y: painted.get(y * w + x, (0, 0, 0)) + (1.0,))
    return canvas


def mark_mask_fitted(w, h, bx, by, bw, bh):
    return coverage(mark_fitted(bx, by, bw, bh), w, h)


def draw_mark_with_shadow(canvas, w, h, bx, by, bw, bh, mark_height):
    mask = mark_mask_fitted(w, h, bx, by, bw, bh)
    shadow = mask_shift(mask, w, h, 0, max(1, int(round(mark_height * 0.035))))
    shadow = mask_blur(shadow, w, h, max(1.0, mark_height * 0.032), passes=2)
    shadow = mask_scale(shadow, 0.34)
    canvas.blit(shadow, lambda x, y: (SHADOW[0], SHADOW[1], SHADOW[2], 1.0))
    shade_glass(canvas, mask, w, h, mark_height)
    return mask


# ---------------------------------------------------------------------------
# Wordmark: original monoline geometric letterforms
# ---------------------------------------------------------------------------
FONT_STROKE = 15.0
FONT_TRACKING = 5.0


def glyph_w():
    skeleton = [(0.0, -100.0), (33.0, 0.0), (66.0, -100.0), (99.0, 0.0), (132.0, -100.0)]
    return [offset_stroke(skeleton, FONT_STROKE, 2.4)], 152.0


def glyph_d():
    stem = offset_stroke([(6.5, -100.0), (6.5, 0.0)], FONT_STROKE)
    bowl = ring(13.0, -50.0, 43.5, FONT_STROKE, -90.0, 90.0)
    return [stem, bowl], 76.0


def glyph_i():
    stem = offset_stroke([(6.5, -70.0), (6.5, 0.0)], FONT_STROKE)
    dot = disc(6.5, -86.5, 6.5)
    return [stem, dot], 28.0


def glyph_l():
    return [offset_stroke([(6.5, -100.0), (6.5, 0.0)], FONT_STROKE)], 26.0


def glyph_space():
    return [], 34.0


def glyph_s():
    anchors = [(58.0, -58.0), (36.0, -63.5), (16.0, -56.0), (20.0, -42.0),
               (34.0, -35.0), (48.0, -27.0), (50.0, -14.0), (36.0, -6.5), (16.0, -12.0)]
    spine = catmull_rom(anchors, samples_per_span=8)
    return [offset_stroke(spine, FONT_STROKE, 1.6)], 76.0


def glyph_p():
    stem = offset_stroke([(6.5, -70.0), (6.5, 24.0)], FONT_STROKE)
    bowl = ring(43.0, -35.0, 28.5, FONT_STROKE)
    return [stem, bowl], 84.0


def glyph_a():
    bowl = ring(35.0, -35.0, 28.5, FONT_STROKE)
    stem = offset_stroke([(63.5, -70.0), (63.5, 0.0)], FONT_STROKE)
    return [bowl, stem], 78.0


def glyph_y():
    return [offset_stroke([(0.0, -70.0), (33.0, 0.0), (33.0, 24.0)], FONT_STROKE)], 46.0


GLYPHS = {
    "W": glyph_w, "D": glyph_d, "i": glyph_i, "l": glyph_l, " ": glyph_space,
    "s": glyph_s, "p": glyph_p, "a": glyph_a, "y": glyph_y,
}


def wordmark(text):
    """Lay out a wordmark: returns (polys, width) with cap height 100."""
    polys = []
    cursor = 0.0
    for index, letter in enumerate(text):
        builder = GLYPHS[letter]
        shapes, advance = builder()
        polys.extend(translate_polys(shapes, cursor, 0.0))
        cursor += advance
        if index != len(text) - 1:
            cursor += FONT_TRACKING
    return polys, cursor


# ---------------------------------------------------------------------------
# Compositions
# ---------------------------------------------------------------------------
def legacy_icon(size):
    canvas = Canvas(size, size)
    radius = size * 0.225
    tile = round_rect(0.0, 0.0, float(size), float(size), radius, segments=14)
    tile_mask = coverage([tile], size, size)
    paint_tile(canvas, size, size, mask=tile_mask, sheen_strength=0.10)
    ring_outer = round_rect(size * 0.012, size * 0.012, size - size * 0.012, size - size * 0.012,
                            radius * 0.95, segments=14)
    ring_inner = round_rect(size * 0.012 + size * 0.010, size * 0.012 + size * 0.010,
                            size - size * 0.012 - size * 0.010, size - size * 0.012 - size * 0.010,
                            radius * 0.9, segments=14)
    ring_mask = mask_and(coverage([ring_outer], size, size), tile_mask)
    inner_mask = coverage([list(reversed(ring_inner))], size, size)
    edge_mask = bytes(max(0, a - b) for a, b in zip(ring_mask, inner_mask))
    canvas.blit(edge_mask, lambda x, y: (TILE_RING[0], TILE_RING[1], TILE_RING[2],
                                         max(0.0, 0.20 - 0.22 * (y / max(1, size - 1)))))
    aspect, _ = mark_aspect()
    mark_w = size * LEGACY_MARK_FRACTION
    mark_h = mark_w / aspect
    box_x = (size - mark_w) / 2
    box_y = (size - mark_h) / 2
    draw_mark_with_shadow(canvas, size, size, box_x, box_y, mark_w, mark_h, mark_h)
    return canvas


def adaptive_background():
    canvas = Canvas(ADAPTIVE, ADAPTIVE)
    paint_tile(canvas, ADAPTIVE, ADAPTIVE, sheen_strength=0.12)
    return canvas


def adaptive_foreground():
    canvas = Canvas(ADAPTIVE, ADAPTIVE)
    aspect, _ = mark_aspect()
    mark_h = SAFE / aspect
    draw_mark_with_shadow(canvas, ADAPTIVE, ADAPTIVE, (ADAPTIVE - SAFE) / 2,
                          (ADAPTIVE - mark_h) / 2, SAFE, mark_h, mark_h)
    return canvas


def adaptive_monochrome():
    canvas = Canvas(ADAPTIVE, ADAPTIVE)
    aspect, _ = mark_aspect()
    mark_h = SAFE / aspect
    mask = coverage(mark_fitted((ADAPTIVE - SAFE) / 2, (ADAPTIVE - mark_h) / 2, SAFE, mark_h),
                    ADAPTIVE, ADAPTIVE)
    canvas.blit(mask, lambda x, y: (255, 255, 255, 1.0))
    return canvas


def tv_banner(w, h):
    canvas = Canvas(w, h)
    paint_tile(canvas, w, h, sheen_strength=0.12)

    wd_polys, _ = wordmark("WD")
    rest_polys, _ = wordmark("Display")
    rest_offset = wordmark("WD")[1] + FONT_TRACKING + 34.0 + FONT_TRACKING
    cap = 100.0                      # wordmark design cap height
    content_w = w * 0.84
    all_words = wd_polys + translate_polys(rest_polys, rest_offset, 0.0)
    wx0, wy0, wx1, wy1 = bbox(scale_polys(all_words, cap / 100.0))
    word_ink_w = wx1 - wx0
    aspect, _ = mark_aspect()

    # Mark height is tied to the cap height; the lockup is then scaled to fit.
    mark_h = cap * 1.30
    mark_w = mark_h * aspect
    gap = cap * 0.34
    lockup_w = mark_w + gap + word_ink_w
    scale = min(1.0, content_w / lockup_w)
    if scale < 1.0:
        mark_h *= scale
        mark_w *= scale
        gap *= scale
        lockup_w *= scale
    left = (w - lockup_w) / 2.0
    center_y = h / 2.0
    mark_top = center_y - mark_h / 2.0
    mark_mask = mark_mask_fitted(w, h, left, mark_top, mark_w, mark_h)
    shadow = mask_shift(mark_mask, w, h, 0, max(1, int(mark_h * 0.035)))
    shadow = mask_blur(shadow, w, h, max(1.0, mark_h * 0.03), passes=2)
    canvas.blit(mask_scale(shadow, 0.30), lambda x, y: (SHADOW[0], SHADOW[1], SHADOW[2], 1.0))
    shade_glass(canvas, mark_mask, w, h, mark_h)

    word_scale = (cap * scale) / 100.0
    # Align the wordmark cap box (design y -100..0) with the mark centre.
    dx = left + mark_w + gap - wx0
    dy = center_y - (-50.0 * word_scale)
    # Two-tone wordmark: the "WD" pair is bright, "Display" is secondary.
    wd_scaled = translate_polys(scale_polys(wd_polys, word_scale), dx, dy)
    rest_scaled = translate_polys(
        scale_polys(translate_polys(rest_polys, rest_offset, 0.0), word_scale), dx, dy)
    cap_top = dy - 100.0 * word_scale
    baseline = dy

    def lit(tone):
        """Same light-from-above logic as the mark, so the lockup reads as one."""
        def paint(x, y):
            t = min(1.0, max(0.0, (y - cap_top) / max(1.0, baseline - cap_top)))
            colour = mix(tone[0], tone[1], t)
            return (colour[0], colour[1], colour[2], 1.0)
        return paint

    canvas.blit(coverage(wd_scaled, w, h), lit(WORDMARK_STRONG))
    canvas.blit(coverage(rest_scaled, w, h), lit(WORDMARK_WEAK))
    return canvas


# ---------------------------------------------------------------------------
# Vector drawable for the notification small icon (also the themed tint glyph)
# ---------------------------------------------------------------------------
def path_data(polys, decimals=3):
    parts = []
    for poly in polys:
        chunks = []
        for index, (x, y) in enumerate(poly):
            command = "M" if index == 0 else "L"
            chunks.append("%s%.*f,%.*f" % (command, decimals, x, decimals, y))
        parts.append(" ".join(chunks) + " Z")
    return " ".join(parts)


def ic_wd_monochrome_svg():
    """24dp vector: the same mark, fitted to 20dp of the 24dp viewport."""
    polys = shear_polys(mark_design(), MARK_SHEAR, MARK_H)
    fitted = fit_polys(polys, 2.0, 2.0, 20.0, 20.0)
    return ("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
            "<!-- Generated by design/art/generate_wd_art.py. Original geometry; not a copy\n"
            "     of any third-party or Apple artwork. Used for the notification small icon\n"
            "     and as the themed-icon hint glyph. -->\n"
            "<vector xmlns:android=\"http://schemas.android.com/apk/res/android\"\n"
            "    android:width=\"24dp\"\n"
            "    android:height=\"24dp\"\n"
            "    android:viewportWidth=\"24\"\n"
            "    android:viewportHeight=\"24\">\n"
            "    <path\n"
            "        android:fillColor=\"#FFFFFFFF\"\n"
            "        android:fillType=\"nonZero\"\n"
            "        android:pathData=\"%s\" />\n"
            "</vector>\n" % path_data(fitted, 2))


def adaptive_icon_xml():
    """Adaptive icon: PNG layers, plus the monochrome layer for themed icons."""
    return ("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
            "<!-- Generated by design/art/generate_wd_art.py. 108dp canvas; key content\n"
            "     (the mark) stays inside the 66dp safe square, so every launcher mask\n"
            "     up to the 108dp circle crops only the tile, never the glyph. -->\n"
            "<adaptive-icon xmlns:android=\"http://schemas.android.com/apk/res/android\">\n"
            "    <background android:drawable=\"@drawable/ic_launcher_background\" />\n"
            "    <foreground android:drawable=\"@drawable/ic_launcher_foreground\" />\n"
            "    <monochrome android:drawable=\"@drawable/ic_launcher_monochrome\" />\n"
            "</adaptive-icon>\n")


def wd_mark_svg():
    """Master geometry sheet: the mark inside a 108x108 adaptive viewport."""
    polys = shear_polys(mark_design(), MARK_SHEAR, MARK_H)
    x0, y0, x1, y1 = bbox(polys)
    mark_h = SAFE * (y1 - y0) / (x1 - x0)
    fitted = fit_polys(polys, (ADAPTIVE - SAFE) / 2, (ADAPTIVE - mark_h) / 2, SAFE, mark_h)
    scaled = scale_polys(fitted, 108.0 / ADAPTIVE)

    def hex_of(colour):
        return "#%02X%02X%02X" % colour

    return ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<!-- WD Display master mark geometry. Original construction; see\n"
            "     design/BRANDING-NOTES.md. No third-party or Apple artwork is copied. -->\n"
            "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"108\" height=\"108\""
            " viewBox=\"0 0 108 108\">\n"
            "  <defs>\n"
            "    <linearGradient id=\"glass\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">\n"
            "      <stop offset=\"0\" stop-color=\"%s\"/>\n"
            "      <stop offset=\"0.5\" stop-color=\"%s\"/>\n"
            "      <stop offset=\"1\" stop-color=\"%s\"/>\n"
            "    </linearGradient>\n"
            "  </defs>\n"
            "  <rect width=\"108\" height=\"108\" rx=\"24\" fill=\"%s\"/>\n"
            "  <path fill=\"url(#glass)\" d=\"%s\"/>\n"
            "</svg>\n" % (hex_of(GLASS_TOP), hex_of(GLASS_MID), hex_of(GLASS_BOTTOM),
                         hex_of(TILE_BOTTOM), path_data(scaled, 3)))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    mipmaps = (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192))
    written = []
    for bucket, size in mipmaps:
        canvas = legacy_icon(size)
        path = os.path.join(RES, "mipmap-%s" % bucket, "ic_launcher.png")
        written.append((path, canvas.save(path), size, size))
    for name, canvas, dims in (("ic_launcher_background", adaptive_background(), (ADAPTIVE, ADAPTIVE)),
                               ("ic_launcher_foreground", adaptive_foreground(), (ADAPTIVE, ADAPTIVE)),
                               ("ic_launcher_monochrome", adaptive_monochrome(), (ADAPTIVE, ADAPTIVE))):
        path = os.path.join(RES, "drawable-xxxhdpi", name + ".png")
        written.append((path, canvas.save(path), dims[0], dims[1]))
    for bucket, dims in (("drawable", (320, 180)), ("drawable-xhdpi", (640, 360))):
        canvas = tv_banner(dims[0], dims[1])
        path = os.path.join(RES, bucket, "tv_banner.png")
        written.append((path, canvas.save(path), dims[0], dims[1]))
    vector_path = os.path.join(RES, "drawable", "ic_wd_monochrome.xml")
    os.makedirs(os.path.dirname(vector_path), exist_ok=True)
    with open(vector_path, "w") as handle:
        handle.write(ic_wd_monochrome_svg())
    written.append((vector_path, os.path.getsize(vector_path), 24, 24))
    adaptive_path = os.path.join(RES, "mipmap-anydpi-v26", "ic_launcher.xml")
    os.makedirs(os.path.dirname(adaptive_path), exist_ok=True)
    with open(adaptive_path, "w") as handle:
        handle.write(adaptive_icon_xml())
    written.append((adaptive_path, os.path.getsize(adaptive_path), 108, 108))
    svg_path = os.path.join(ART, "wd-mark.svg")
    os.makedirs(ART, exist_ok=True)
    with open(svg_path, "w") as handle:
        handle.write(wd_mark_svg())
    written.append((svg_path, os.path.getsize(svg_path), 108, 108))

    for path, size, w, h in written:
        print("%-72s %8d bytes  %sx%s" % (os.path.relpath(path, ROOT), size, w, h))


if __name__ == "__main__":
    main()
