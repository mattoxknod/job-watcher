"""Fetch each employer's logo once, so the site can show them offline.

Run when the watch list changes; the PNGs it writes are committed.

    uv run python scripts/fetch_logos.py

The logos are stored in the repository rather than loaded from a logo service
at run time, for two reasons: the installed app has to work with no network,
and a run-time lookup would tell a third party which companies are being
looked at every time a page opens.

Each file is the company's own site icon, used to identify that company beside
its own job postings. A company whose icon cannot be fetched simply has no
file, and the site falls back to its initials.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobwatcher.sources import SOURCES  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "assets" / "logos"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

#: Resolves a domain's site icon and returns a PNG at the size asked for,
#: which saves having to parse each site's HTML and convert .ico files.
ENDPOINT = "https://www.google.com/s2/favicons?sz=128&domain={domain}"

#: Below this there is no image at all. Kept low on purpose: a simple mark
#: like BlackRock's "B" is a perfectly good logo in a couple of hundred bytes.
MIN_BYTES = 100

#: Which image the bytes actually are, whatever the request asked for. The
#: service answers with JPEG about as often as PNG.
SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"GIF8", "gif"),
    (b"<svg", "svg"),
)


def image_kind(data: bytes) -> str | None:
    """The file extension these bytes deserve, or None if they are not an image."""
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    for magic, kind in SIGNATURES:
        if data.startswith(magic):
            return kind
    return None


def fetch(domain: str) -> bytes | None:
    request = urllib.request.Request(
        ENDPOINT.format(domain=domain), headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"  ! {domain}: {exc}")
        return None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index: dict[str, str] = {}
    skipped: list[str] = []

    for source in SOURCES:
        domain = source.get("domain")
        if not domain:
            continue

        data = fetch(domain)
        kind = image_kind(data) if data else None
        if not data or kind is None or len(data) < MIN_BYTES:
            size = len(data) if data else 0
            print(f"  - {source['name']:<24} no usable icon ({size} bytes)")
            skipped.append(source["name"])
            continue

        filename = f"{source['name']}.{kind}"
        (OUT / filename).write_bytes(data)
        index[source["name"]] = filename
        print(f"  + {source['name']:<24} {len(data):>6,} bytes  {filename}")

    # The site reads this to know which logos exist, so a company without one
    # shows its initials instead of asking for a file that is not there.
    (OUT / "index.json").write_text(
        json.dumps(dict(sorted(index.items())), indent=2) + "\n", encoding="utf-8"
    )

    print(f"\n{len(index)} logos written to {OUT}")
    if skipped:
        print(f"showing initials instead: {', '.join(skipped)}")


if __name__ == "__main__":
    main()
