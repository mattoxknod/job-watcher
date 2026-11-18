"""Build the US state outlines the map page draws.

Run once; the file it writes is committed. The map has to work in an installed
app with no network, so the geometry is vendored here rather than fetched from
a CDN at run time, and the page draws it with plain SVG instead of a mapping
library.

    uv run python scripts/build_map.py

Source: the Census-derived public-domain state boundaries published at
https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json

The projection is Albers equal-area conic, the standard choice for a map of the
United States, with Alaska, Hawaii and Puerto Rico drawn as insets on their own
parallels. Equal-area matters here: the map colours states by how many postings
they hold, and a projection that inflated the northern states would overstate
them.
"""

from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

SOURCE = (
    "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/"
    "master/data/geojson/us-states.json"
)

OUT = Path(__file__).resolve().parents[1] / "assets" / "us-states.json"

WIDTH, HEIGHT = 960, 600

#: Each group gets its own standard parallels and central meridian, and its own
#: box on the canvas: (x, y, width, height).
GROUPS = {
    "main": {"lon0": -96.0, "parallels": (29.5, 45.5), "box": (108, 14, 844, 496)},
    "AK": {"lon0": -152.0, "parallels": (55.0, 65.0), "box": (14, 386, 210, 196)},
    "HI": {"lon0": -157.0, "parallels": (8.0, 18.0), "box": (246, 494, 128, 88)},
    "PR": {"lon0": -66.4, "parallels": (17.0, 19.0), "box": (820, 536, 118, 48)},
}

#: Census FIPS ids in the source file, mapped to the postal codes the history
#: file uses.
FIPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
    "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY", "72": "PR",
}

INSETS = {"AK", "HI", "PR"}

#: Drop a point closer than this to the one before it, in final pixels. Keeps
#: the file small without a visible change to the outlines.
MIN_STEP = 0.4


def albers(lon: float, lat: float, lon0: float, parallels: tuple[float, float]):
    """Albers equal-area conic. Returns map units with y increasing north."""
    phi1, phi2 = (math.radians(p) for p in parallels)
    lam = math.radians(lon - lon0)
    phi = math.radians(lat)

    n = (math.sin(phi1) + math.sin(phi2)) / 2
    c = math.cos(phi1) ** 2 + 2 * n * math.sin(phi1)
    rho = math.sqrt(max(c - 2 * n * math.sin(phi), 0)) / n
    rho0 = math.sqrt(c) / n

    return rho * math.sin(n * lam), rho0 - rho * math.cos(n * lam)


def rings_of(geometry: dict) -> list[list[list[float]]]:
    """Every outer ring of a Polygon or MultiPolygon."""
    if geometry["type"] == "Polygon":
        return geometry["coordinates"]
    rings = []
    for polygon in geometry["coordinates"]:
        rings.extend(polygon)
    return rings


def ring_area_centroid(points: list[tuple[float, float]]):
    """Signed area and centroid of a closed ring."""
    area = cx = cy = 0.0
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if area == 0:
        return 0.0, points[0]
    area /= 2
    return abs(area), (cx / (6 * area), cy / (6 * area))


def fit(groups: dict[str, list], box: tuple[float, float, float, float]):
    """Scale and translate projected rings to fill a box, keeping the shape."""
    xs = [x for rings in groups.values() for ring in rings for x, _ in ring]
    ys = [y for rings in groups.values() for ring in rings for _, y in ring]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)

    bx, by, bw, bh = box
    span_x = maxx - minx or 1
    span_y = maxy - miny or 1
    scale = min(bw / span_x, bh / span_y)

    # Centre inside the box, and flip y so north is up on screen.
    off_x = bx + (bw - span_x * scale) / 2
    off_y = by + (bh - span_y * scale) / 2

    def place(x: float, y: float) -> tuple[float, float]:
        return (off_x + (x - minx) * scale, off_y + (maxy - y) * scale)

    return place


def to_path(rings: list[list[tuple[float, float]]]) -> str:
    """One SVG path for a state, thinning points as it goes."""
    parts = []
    for ring in rings:
        kept: list[tuple[float, float]] = []
        for x, y in ring:
            if kept:
                px, py = kept[-1]
                if abs(x - px) < MIN_STEP and abs(y - py) < MIN_STEP:
                    continue
            kept.append((round(x, 1), round(y, 1)))
        if len(kept) < 3:
            continue
        parts.append(
            "M" + "L".join(f"{x},{y}" for x, y in kept) + "Z"
        )
    return "".join(parts)


def main() -> None:
    print(f"fetching {SOURCE}")
    with urllib.request.urlopen(SOURCE, timeout=60) as response:
        data = json.load(response)

    # Project every state in its group's own parallels first, then fit each
    # group to its box as a whole so the insets keep their relative shapes.
    projected: dict[str, dict] = {}
    by_group: dict[str, dict[str, list]] = {name: {} for name in GROUPS}

    for feature in data["features"]:
        code = FIPS.get(str(feature.get("id")))
        if not code:
            continue
        group = code if code in INSETS else "main"
        spec = GROUPS[group]
        rings = [
            [albers(lon, lat, spec["lon0"], spec["parallels"]) for lon, lat in ring]
            for ring in rings_of(feature["geometry"])
        ]
        by_group[group][code] = rings
        projected[code] = {"name": feature["properties"]["name"], "group": group}

    states: dict[str, dict] = {}
    for group, members in by_group.items():
        if not members:
            continue
        place = fit(members, GROUPS[group]["box"])
        for code, rings in members.items():
            screen = [[place(x, y) for x, y in ring] for ring in rings]
            biggest = max(screen, key=lambda r: ring_area_centroid(r)[0])
            _, (cx, cy) = ring_area_centroid(biggest)
            states[code] = {
                "name": projected[code]["name"],
                "inset": group in INSETS,
                "cx": round(cx, 1),
                "cy": round(cy, 1),
                "d": to_path(screen),
            }

    out = {
        "width": WIDTH,
        "height": HEIGHT,
        "projection": "Albers equal-area conic, with Alaska, Hawaii and Puerto "
                      "Rico as insets",
        "source": SOURCE,
        "states": dict(sorted(states.items())),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")

    size = OUT.stat().st_size
    print(f"wrote {OUT.name}: {len(states)} states, {size:,} bytes")


if __name__ == "__main__":
    main()
