"""One place for the outbound HTTP calls.

Boards are read politely. Workday caps a page at 20 postings, so a board with
two thousand openings takes a hundred requests, and several of these tenants
answer 429 when those arrive back to back. Two things keep that from failing a
source: a minimum gap between requests to the same host, and a retry that waits
out a 429 properly, honouring ``Retry-After`` when the server sends one.
"""

from __future__ import annotations

import random
import time
from urllib.parse import urlsplit

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

TIMEOUT = 45

#: Attempts per request, including the first.
RETRIES = 5

#: Seconds to wait after an ordinary failure, growing per attempt.
BACKOFF = 2.0

#: Seconds to wait after a 429 when the server names no Retry-After.
RATE_LIMIT_BACKOFF = [10.0, 25.0, 45.0, 75.0]

#: Never sleep longer than this on one wait, however large Retry-After is.
MAX_SLEEP = 120.0

#: Minimum gap between two requests to the same host.
MIN_INTERVAL = 0.45

_last_call: dict[str, float] = {}


class FetchError(RuntimeError):
    """A source could not be read. The run records it and carries on."""


def _throttle(url: str) -> None:
    """Hold off until this host's minimum gap has passed."""
    host = urlsplit(url).netloc
    previous = _last_call.get(host)
    now = time.monotonic()
    if previous is not None:
        wait = MIN_INTERVAL - (now - previous)
        if wait > 0:
            time.sleep(wait)
    _last_call[host] = time.monotonic()


def _retry_after(response) -> float | None:
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        return min(float(value), MAX_SLEEP)
    except ValueError:
        return None


def _request(method: str, url: str, **kwargs) -> dict:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        **kwargs.pop("headers", {}),
    }
    last = None
    rate_limited = 0

    for attempt in range(RETRIES):
        _throttle(url)
        try:
            response = requests.request(
                method, url, headers=headers, timeout=TIMEOUT, **kwargs
            )

            if response.status_code == 429:
                last = requests.HTTPError(f"429 Too Many Requests for {url}")
                wait = _retry_after(response)
                if wait is None:
                    index = min(rate_limited, len(RATE_LIMIT_BACKOFF) - 1)
                    wait = RATE_LIMIT_BACKOFF[index]
                rate_limited += 1
                if attempt < RETRIES - 1:
                    # Jitter so a run's sources do not all retry in lockstep.
                    time.sleep(wait + random.uniform(0, 2.0))
                continue

            response.raise_for_status()
            return response.json()

        except Exception as exc:  # noqa: BLE001 - every failure is retried alike
            last = exc
            if attempt < RETRIES - 1:
                time.sleep(BACKOFF * (attempt + 1) + random.uniform(0, 1.0))

    raise FetchError(f"{method} {url} failed: {last}") from last


def get_json(url: str, params: dict | None = None) -> dict:
    return _request("GET", url, params=params)


def post_json(url: str, body: dict) -> dict:
    return _request(
        "POST", url, json=body, headers={"Content-Type": "application/json"}
    )
