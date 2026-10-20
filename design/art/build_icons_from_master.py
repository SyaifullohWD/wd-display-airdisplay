#!/usr/bin/env python3
"""Regenerate the WD Display icon set from the designer's 1024x1024 master.

The master is a full-bleed tile: a soft periwinkle gradient with a translucent
glass W. The background is part of the identity, so the adaptive icon is built
with a "safe composition": the artwork is placed at the 72dp viewport inside the
108dp layer and the ring around it is filled with a blurred extension of the
same gradient, so a launcher mask crops only the ring and the visible result is
the artwork exactly as authored, off-center balance included.

Run: python3 design/art/build_icons_from_master.py "<path to master png>"
"""

import sys
from PIL import Image, ImageFilter
import pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
RES = ROOT / "app/src/main/res"

# Android density buckets: legacy launcher PNGs.
LEGACY = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}
# Adaptive layers are 108dp. At xxxhdpi that is 432px; the 72dp viewport is 288px.
ADAPTIVE_PX = 432
# Launchers draw the 108dp adaptive canvas and mask it, but the visible icon is the
# 72dp viewport, so the artwork has to sit at 72/108 of the canvas or it renders
# enlarged. Everything outside that 288px block is the clamped edge extension the
# mask crops, which keeps the gradient continuous with no seam.
VIEWPORT_PX = 288
ART_PX = VIEWPORT_PX


def rounded_mask(size: int, radius_ratio: float = 0.225) -> Image.Image:
    """Squircle-ish rounded square, close to the iOS/One UI launcher silhouette."""
    scale = 4
    big = Image.new("L", (size * scale, size * scale), 0)
    radius = int(size * scale * radius_ratio)
    from PIL import ImageDraw

    ImageDraw.Draw(big).rounded_rectangle(
        (0, 0, size * scale - 1, size * scale - 1), radius=radius, fill=255
    )
    return big.resize((size, size), Image.LANCZOS)


def legacy_icon(master: Image.Image, size: int) -> Image.Image:
    icon = master.resize((size, size), Image.LANCZOS).convert("RGBA")
    icon.putalpha(rounded_mask(size))
    return icon


def edge_extend(tile: Image.Image, size: int) -> Image.Image:
    """Fill a larger canvas by clamping to the tile's own edge pixels.

    Clamping (rather than blurring or flat-filling) keeps the ring pixel-continuous
    with the tile border, so a launcher mask shows no seam against the artwork's
    own gradient.
    """
    import numpy as np

    t = np.asarray(tile.convert("RGBA"))
    th, tw = t.shape[:2]
    offset = (size - tw) // 2
    xs = np.clip(np.arange(size) - offset, 0, tw - 1)
    ys = np.clip(np.arange(size) - offset, 0, th - 1)
    out = t[ys][:, xs]
    return Image.fromarray(out, mode="RGBA")


def adaptive_foreground(master: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", (ADAPTIVE_PX, ADAPTIVE_PX), (0, 0, 0, 0))
    art = master.resize((VIEWPORT_PX, VIEWPORT_PX), Image.LANCZOS).convert("RGBA")
    offset = (ADAPTIVE_PX - VIEWPORT_PX) // 2
    canvas.paste(art, (offset, offset))
    return canvas


def banner(master: Image.Image, width: int, height: int) -> Image.Image:
    tile_h = int(height * 0.78)
    tile = master.resize((tile_h, tile_h), Image.LANCZOS).convert("RGBA")
    mask = rounded_mask(tile_h, 0.20)
    canvas = edge_extend(tile, max(width, height)).resize((width, height), Image.LANCZOS)
    canvas.alpha_composite(tile, ((width - tile_h) // 2, (height - tile_h) // 2))
    return canvas


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('usage: build_icons_from_master.py "<master.png>"')
    master = Image.open(sys.argv[1]).convert("RGB")
    if master.width != master.height:
        raise SystemExit("master must be square")

    for folder, size in LEGACY.items():
        path = RES / folder / "ic_launcher.png"
        legacy_icon(master, size).save(path)
        print(f"{path.relative_to(ROOT)}  {size}x{size}")

    adaptive_foreground(master).save(RES / "drawable-xxxhdpi/ic_launcher_foreground.png")
    edge_extend(master.resize((VIEWPORT_PX, VIEWPORT_PX), Image.LANCZOS).convert("RGBA"), ADAPTIVE_PX).save(
        RES / "drawable-xxxhdpi/ic_launcher_background.png"
    )
    print("adaptive layers 432x432 written (foreground, background)")
    print("no monochrome layer by design: themed icons are opted out")

    banner(master, 320, 180).save(RES / "drawable/tv_banner.png")
    banner(master, 640, 360).save(RES / "drawable-xhdpi/tv_banner.png")
    print("tv banners 320x180 and 640x360 written")

    master.resize((512, 512), Image.LANCZOS).convert("RGB").save(ROOT / "release/icon.png")
    print("release/icon.png 512x512 written")


if __name__ == "__main__":
    main()
