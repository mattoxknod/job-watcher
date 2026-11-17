"""Generate the app icons the web app manifest points at.

Run once; the PNGs it writes are committed. Chrome wants a 192px and a 512px
icon before it will offer to install a site, and a maskable copy so the icon
still reads inside Android's circle mask.

    uv run python scripts/make_icons.py
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets"

BACKGROUND = (26, 42, 66)       # deep navy, reads on both light and dark docks
BAR_BLUE = (57, 135, 229)
BAR_ORANGE = (235, 104, 52)

#: Three bars, as fractions of the icon box: x, width, top, colour.
BARS = [
    (0.16, 0.18, 0.56, BAR_BLUE),
    (0.41, 0.18, 0.37, BAR_BLUE),
    (0.66, 0.18, 0.20, BAR_ORANGE),
]

BAR_BOTTOM = 0.82


def _rounded(x: int, y: int, size: int, radius: float) -> bool:
    """True when the pixel is inside a rounded square."""
    for cx, cy in (
        (radius, radius),
        (size - radius, radius),
        (radius, size - radius),
        (size - radius, size - radius),
    ):
        inside_x = (x < radius) if cx == radius else (x > size - radius)
        inside_y = (y < radius) if cy == radius else (y > size - radius)
        if inside_x and inside_y:
            return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2
    return True


def render(size: int, maskable: bool = False) -> bytes:
    """Draw the icon and return it as PNG bytes."""
    # A maskable icon keeps its art inside the safe circle, so it is drawn at
    # 60% scale on a full-bleed square.
    scale = 0.62 if maskable else 1.0
    radius = 0.0 if maskable else size * 0.22
    inset = size * (1 - scale) / 2

    rows = []
    for y in range(size):
        row = bytearray([0])  # PNG filter: none
        for x in range(size):
            if not maskable and not _rounded(x, y, size, radius):
                row += bytes((0, 0, 0, 0))
                continue

            colour = BACKGROUND
            # Map the pixel into the art box.
            ax = (x - inset) / (size * scale)
            ay = (y - inset) / (size * scale)
            if 0 <= ax <= 1 and 0 <= ay <= 1:
                for bx, bw, btop, bcol in BARS:
                    if bx <= ax <= bx + bw and btop <= ay <= BAR_BOTTOM:
                        colour = bcol
                        break
            row += bytes((*colour, 255))
        rows.append(bytes(row))

    raw = b"".join(rows)

    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(
            ">I", zlib.crc32(body) & 0xFFFFFFFF
        )

    header = struct.pack(">2I5B", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        path = ASSETS / f"icon-{size}.png"
        path.write_bytes(render(size))
        print(f"wrote {path.name} ({path.stat().st_size:,} bytes)")

    path = ASSETS / "icon-maskable-512.png"
    path.write_bytes(render(512, maskable=True))
    print(f"wrote {path.name} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
