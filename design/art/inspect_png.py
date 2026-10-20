#!/usr/bin/env python3
"""Stdlib PNG inspector used to verify generated artwork (no Pillow available).

Reports for each file: pixel size, colour type, alpha statistics, the bounding
box of visible ink, the ink fraction, and a coarse ASCII preview so a blank,
clipped or off-centre render is obvious.

Usage:  python3 design/art/inspect_png.py FILE [FILE ...] [--preview]
        python3 design/art/inspect_png.py FILE --zoom 8 [--out OUT.png]

--zoom writes a nearest-neighbour enlargement (to OUT, default FILE.zoom.png) so
small raster assets can be eyeballed at review size.
"""

import struct
import sys
import zlib

RAMP = " .:-=+*#%@"


def write_png(path, width, height, rgba, include_alpha=True):
    colour_type = 6 if include_alpha else 2
    channels = 4 if include_alpha else 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        row = rgba[y * width * 4:(y + 1) * width * 4]
        if include_alpha:
            raw += row
        else:
            for x in range(width):
                raw += row[x * 4:x * 4 + 3]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, 8, colour_type, 0, 0, 0)
    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                     + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def to_rgba(rows, width, height, colour):
    out = bytearray()
    for y in range(height):
        row = rows[y]
        for x in range(width):
            if colour == 6:
                out += row[x * 4:x * 4 + 4]
            elif colour == 2:
                out += row[x * 3:x * 3 + 3] + b"\xff"
            elif colour == 4:
                out += bytes([row[x * 2]] * 3) + row[x * 2 + 1:x * 2 + 2]
            else:
                out += bytes([row[x]] * 3) + b"\xff"
    return bytes(out)


def zoom(source, factor, target):
    width, height, colour, rows = read_png(source)
    rgba = to_rgba(rows, width, height, colour)
    big_w, big_h = width * factor, height * factor
    out = bytearray(big_w * big_h * 4)
    for y in range(height):
        line = bytearray()
        for x in range(width):
            line += rgba[(y * width + x) * 4:(y * width + x) * 4 + 4] * factor
        for repeat in range(factor):
            start = ((y * factor + repeat) * big_w) * 4
            out[start:start + big_w * 4] = line
    write_png(target, big_w, big_h, bytes(out))
    print("%s -> %s (%dx%d, zoom x%d)" % (source, target, big_w, big_h, factor))


def read_png(path):
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG: " + path)
    pos = 8
    width = height = depth = colour = interlace = None
    idat = bytearray()
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if tag == b"IHDR":
            width, height, depth, colour, _, _, interlace = struct.unpack(">IIBBBBB", payload)
        elif tag == b"IDAT":
            idat += payload
        elif tag == b"IEND":
            break
    if depth != 8 or interlace != 0 or colour not in (0, 2, 4, 6):
        raise ValueError("unsupported PNG (depth=%s colour=%s interlace=%s)"
                         % (depth, colour, interlace))
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[colour]
    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    previous = bytearray(stride)
    rows = []
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        line = bytearray(raw[offset:offset + stride])
        offset += stride
        for index in range(stride):
            left = line[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                line[index] = (line[index] + left) & 0xFF
            elif filter_type == 2:
                line[index] = (line[index] + up) & 0xFF
            elif filter_type == 3:
                line[index] = (line[index] + ((left + up) >> 1)) & 0xFF
            elif filter_type == 4:
                estimate = left + up - upper_left
                pa, pb, pc = abs(estimate - left), abs(estimate - up), abs(estimate - upper_left)
                nearest = left if (pa <= pb and pa <= pc) else (up if pb <= pc else upper_left)
                line[index] = (line[index] + nearest) & 0xFF
        rows.append(bytes(line))
        previous = line
    return width, height, colour, rows


def analyse(path, preview=False):
    width, height, colour, rows = read_png(path)
    transparent = partial = opaque = 0
    min_x, min_y, max_x, max_y = width, height, -1, -1
    luminance = [[0.0] * width for _ in range(height)]
    for y, row in enumerate(rows):
        for x in range(width):
            if colour == 6:
                red, green, blue, alpha = row[x * 4:x * 4 + 4]
            elif colour == 2:
                red, green, blue = row[x * 3:x * 3 + 3]
                alpha = 255
            elif colour == 4:
                red = green = blue = row[x * 2]
                alpha = row[x * 2 + 1]
            else:
                red = green = blue = alpha = row[x]
            if alpha == 0:
                transparent += 1
            elif alpha == 255:
                opaque += 1
            else:
                partial += 1
            if alpha > 8:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
            luminance[y][x] = (0.2126 * red + 0.7152 * green + 0.0722 * blue) * (alpha / 255.0)
    total = width * height
    kind = {0: "gray", 2: "rgb", 4: "gray+alpha", 6: "rgba"}[colour]
    print("%s" % path)
    print("  size            %dx%d (%s, 8-bit)" % (width, height, kind))
    print("  alpha           transparent=%d (%.1f%%) partial=%d opaque=%d"
          % (transparent, 100.0 * transparent / total, partial, opaque))
    if max_x >= 0:
        print("  ink bbox        x %d..%d (%d wide), y %d..%d (%d tall), margins L/R/T/B %d/%d/%d/%d"
              % (min_x, max_x, max_x - min_x + 1, min_y, max_y, max_y - min_y + 1,
                 min_x, width - 1 - max_x, min_y, height - 1 - max_y))
        ink = sum(1 for y in range(height) for x in range(width)
                  if (rows[y][x * 4 + 3] if colour == 6 else 255) > 8)
        print("  ink fraction    %.1f%% of the canvas" % (100.0 * ink / total))
    else:
        print("  ink bbox        EMPTY (fully transparent)")
    if preview:
        print(preview_text(luminance, width, height))
    return width, height


def preview_text(luminance, width, height, columns=64, rows_out=24):
    """Coarse ASCII render: bright ink on a dark field becomes visible glyphs."""
    lines = []
    for row in range(rows_out):
        y0 = row * height // rows_out
        y1 = max(y0 + 1, (row + 1) * height // rows_out)
        text = []
        for col in range(columns):
            x0 = col * width // columns
            x1 = max(x0 + 1, (col + 1) * width // columns)
            total = 0.0
            count = 0
            for y in range(y0, y1):
                for x in range(x0, x1):
                    total += luminance[y][x]
                    count += 1
            value = total / max(1, count)
            text.append(RAMP[min(len(RAMP) - 1, int(value / 256.0 * len(RAMP)))])
        lines.append("".join(text).rstrip())
    return "\n".join("  " + line for line in lines)


if __name__ == "__main__":
    argv = sys.argv[1:]
    show = "--preview" in argv
    argv = [a for a in argv if a != "--preview"]
    factor = None
    output = None
    if "--zoom" in argv:
        index = argv.index("--zoom")
        factor = int(argv[index + 1])
        argv = argv[:index] + argv[index + 2:]
    if "--out" in argv:
        index = argv.index("--out")
        output = argv[index + 1]
        argv = argv[:index] + argv[index + 2:]
    for name in argv:
        analyse(name, preview=show)
        if factor:
            zoom(name, factor, output or name + ".zoom.png")
