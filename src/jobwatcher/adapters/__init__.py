"""Per-applicant-tracking-system readers.

Each adapter exposes two functions:

``fetch(source)``
    Call the board and return the raw payload exactly as it came back. The
    result is what gets written to ``data/raw/<date>/<source>.json.gz``.

``normalize(source, raw)``
    Turn that payload into a list of postings in the common columns. It must be
    a pure function of the raw payload so the history rebuilds identically.
"""

from jobwatcher.adapters import amazon, oracle, workday

ADAPTERS = {
    "workday": workday,
    "amazon": amazon,
    "oracle": oracle,
}


def for_source(source: dict):
    """Return the adapter module that reads ``source``."""
    try:
        return ADAPTERS[source["kind"]]
    except KeyError:
        raise ValueError(f"no adapter for kind {source['kind']!r}") from None
