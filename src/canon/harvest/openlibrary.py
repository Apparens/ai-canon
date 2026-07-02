"""CAN-10/11 — OpenLibrary harvester (edition_count for books).

OpenLibrary (Internet Archive) is free, needs no key, and its catalogue data is
open. It supplies a book-appropriate signal the paper harvester cannot: the
edition_count, i.e. the number of distinct catalogued editions and printings of a
work. That is a reproducible proxy for sustained adoption and longevity, since a
book reissued many times over years has kept being adopted. Each work's search
response is written to the write-once raw cache; metrics are derived from the
cache by parse(), so a release rebuilds offline and deterministically (rule 3),
and a miss is a declared gap, never an imputed number (rule 8).

Book matching by title alone is collision-prone (which is why book harvesting was
deferred), so a candidate must clear a title-overlap bar AND share an author with
the seed record before its edition_count is taken; otherwise the work is a
declared gap. Only English-language books are queried: scoring a Chinese-language
work against an English-centric catalogue would be the cross-language comparison
the method defers (rule 5), so non-English books are left for their own ecosystem.
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .. import raw

_MAX_RESPONSE_BYTES = 20_000_000  # refuse a ballooned API response

SOURCE = "openlibrary"
API = "https://openlibrary.org/search.json"
USER_AGENT = "AI-Canon/0.3 (https://apparens.nl/ai-canon; mailto:office@apparens.nl)"
LICENSE_NOTE = "OpenLibrary, Open Data"
RETRIEVED_AT = "2026-06-30"  # pinned harvest date for this snapshot
_MIN_TITLE_OVERLAP = 0.6
_PACE_SECONDS = 0.15

_SEEDS = Path(__file__).resolve().parents[3] / "data" / "seeds"


def _norm(text) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFC", str(text)).casefold()
    t = re.sub(r"[^\w\s]", " ", t)  # punctuation (colon, comma) -> space so tokens match
    return " ".join(t.split())


def _overlap(a: str, b: str) -> float:
    ta, tb = set(_norm(a).split()), set(_norm(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _title_score(a: str, b: str) -> float:
    """Title similarity tolerant of subtitles: the better of Jaccard and the
    coverage of the shorter title (OpenLibrary often stores only the main title,
    while the seed carries the full subtitle). The author-match requirement in
    _pick is what guards this looser measure against false positives."""
    ta, tb = set(_norm(a).split()), set(_norm(b).split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    jac = inter / len(ta | tb)
    cov = inter / min(len(ta), len(tb))
    return max(jac, cov)


def load_books() -> list[dict]:
    return json.loads((_SEEDS / "books.json").read_text(encoding="utf-8"))


def _cache_name(book_id: str) -> str:
    return f"{book_id}.json"


def _search_title(title: str) -> str:
    """Reduce a title to plain search words. For the bilingual Chinese titles the
    parenthetical is irrelevant (those books are skipped anyway)."""
    base = title.split(" (")[0]
    cleaned = "".join(c if (c.isalnum() or c.isspace()) else " " for c in str(base))
    return " ".join(cleaned.split())


def _first_author(book: dict) -> str:
    author = (book.get("editorial") or {}).get("author", "") or ""
    # seed authors look like "Stuart Russell, Peter Norvig" or "Zhou ... (周志华)"
    return author.split("(")[0].split(",")[0].split("、")[0].strip()


def fetch(book: dict, *, allow_network: bool = True) -> dict | None:
    """Cached/fetched OpenLibrary search response for a book, or None.

    Reads the write-once cache first; only hits the network if allowed and cold.
    Network/HTTP errors return None (a declared gap), never crash.
    """
    name = _cache_name(book["id"])
    cached = raw.read(SOURCE, name)
    if cached is not None:
        return json.loads(cached)
    if not allow_network:
        return None

    title = _search_title(book["canonical_title"])
    if not title:
        return None
    # A general q= query with title AND author surfaces the canonical, most-held
    # work; OpenLibrary's title= index instead floats self-published knockoffs
    # with identical titles to the top, which the author guard would (correctly)
    # reject, leaving real works as false gaps.
    q = (title + " " + _first_author(book)).strip()
    query = {
        "q": q,
        "fields": "key,title,author_name,edition_count,first_publish_year",
        "limit": "5",
    }
    url = f"{API}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read(_MAX_RESPONSE_BYTES + 1).decode("utf-8")
            if len(body.encode("utf-8")) > _MAX_RESPONSE_BYTES:
                raise ValueError(f"response exceeds {_MAX_RESPONSE_BYTES} bytes; refusing to cache")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return None
    finally:
        time.sleep(_PACE_SECONDS)
    raw.write_once(SOURCE, name, body)
    return json.loads(body)


def _author_match(book: dict, doc: dict) -> bool:
    seed = _norm(_first_author(book))
    if not seed:
        return False
    names = [_norm(n) for n in (doc.get("author_name") or [])]
    # surname-or-fullname containment in either direction
    return any(n and (n in seed or seed in n or _overlap(seed, n) >= 0.5) for n in names)


def _pick(book: dict, response: dict) -> dict | None:
    """Choose the catalogue record for this book, or None if none is safe.

    A candidate must clear the title bar AND share an author. Among those, take
    the one with the most editions (the canonical, most-reissued record); ties
    break by title similarity then a stable key. No author match means no pick,
    so a same-title different-book cannot contribute a number.
    """
    docs = (response or {}).get("docs") or []
    qualified = []
    for d in docs:
        sim = _title_score(book["canonical_title"].split(" (")[0], d.get("title"))
        if sim < _MIN_TITLE_OVERLAP:
            continue
        if not _author_match(book, d):
            continue
        if d.get("edition_count") in (None, 0):
            continue
        qualified.append((d, sim))
    if not qualified:
        return None
    best, sim = max(
        qualified,
        key=lambda t: (t[0].get("edition_count") or 0, t[1], str(t[0].get("key") or "")),
    )
    best["_title_sim"] = sim
    return best


def parse(book: dict, response: dict | None) -> dict:
    """Derive the edition_count metric (or a declared gap) from a cached response."""
    if (book.get("language") or "").lower() != "en":
        return {"metrics": [], "gaps": [{"metric": "*", "reason": "non-English work; left for its own ecosystem, not matched against the English-centric OpenLibrary catalogue"}]}
    if response is None:
        return {"metrics": [], "gaps": [{"metric": "*", "reason": "no cached OpenLibrary response (offline / not harvested)"}]}
    match = _pick(book, response)
    if match is None:
        return {"metrics": [], "gaps": [{"metric": "edition_count", "reason": "no OpenLibrary record cleared the title-and-author match"}]}
    sim = match.get("_title_sim", 0.0)
    fy = match.get("first_publish_year")
    year_ok = (not book.get("year")) or (not fy) or abs((book["year"] or 0) - fy) <= 5
    conf = "high" if sim >= 0.85 and year_ok else "medium"
    metric = {
        "work_id": book["id"],
        "metric_name": "edition_count",
        "value": float(match.get("edition_count") or 0),
        "source": "OpenLibrary",
        "retrieved_at": RETRIEVED_AT,
        "confidence": conf,
        "provenance_url": "https://openlibrary.org" + (match.get("key") or ""),
        "license_note": LICENSE_NOTE,
    }
    return {"metrics": [metric], "gaps": []}


def harvest(limit: int | None = None, *, allow_network: bool = True) -> dict:
    """Populate the cache for books and report coverage. Metrics are derived by
    assembly from the cache, not written here."""
    books = load_books()
    if limit:
        books = books[:limit]
    fetched = cached = gaps = skipped = 0
    for book in books:
        if (book.get("language") or "").lower() != "en":
            skipped += 1
            continue
        had_cache = raw.exists(SOURCE, _cache_name(book["id"]))
        resp = fetch(book, allow_network=allow_network)
        if resp is None:
            gaps += 1
            continue
        if had_cache:
            cached += 1
        else:
            fetched += 1
    report = {
        "books_considered": len(books),
        "newly_fetched": fetched,
        "served_from_cache": cached,
        "uncovered": gaps,
        "non_english_skipped": skipped,
    }
    print(json.dumps(report, indent=2))
    return report


def _main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="OpenLibrary harvester (books)")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--offline", action="store_true", help="cache-only, no network")
    args = p.parse_args(argv)
    harvest(limit=args.limit, allow_network=not args.offline)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
