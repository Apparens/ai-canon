"""CAN-09 — OpenAlex harvester (citation_count for papers).

OpenAlex is free, CC0, and needs no key. The harvester is polite (descriptive
User-Agent with a mailto, paced requests) and writes each work's API response to
the write-once raw cache. Metrics are derived from the cache by `parse()`, so:

  * re-running reads the cache and never re-hits the network (deterministic),
  * offline with no cache yields a declared GAP, never a fabricated number (rule 8),
  * the cached snapshot is the pinned evidence a release is rebuilt from.

Book harvesting by title is noisier (title collisions) and is deferred; this
harvester targets the 162 papers, where OpenAlex coverage is strong.
"""

from __future__ import annotations

import json
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .. import raw

SOURCE = "openalex"
API = "https://api.openalex.org/works"
USER_AGENT = "AI-Canon/0.3 (https://apparens.nl/ai-canon; mailto:office@apparens.nl)"
LICENSE_NOTE = "OpenAlex, CC0 metadata"
RETRIEVED_AT = "2026-06-29"  # pinned harvest date for this snapshot
_MIN_TITLE_OVERLAP = 0.6
_PACE_SECONDS = 0.12

_SEEDS = Path(__file__).resolve().parents[3] / "data" / "seeds"


def _norm(text) -> str:
    if not text:
        return ""
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


def _overlap(a: str, b: str) -> float:
    ta, tb = set(_norm(a).split()), set(_norm(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def load_papers() -> list[dict]:
    return json.loads((_SEEDS / "papers.json").read_text(encoding="utf-8"))


def _cache_name(paper_id: str) -> str:
    return f"{paper_id}.json"


def _search_terms(title: str) -> str:
    """OpenAlex filter values treat commas as filter separators and choke on
    other punctuation, so reduce a title to plain search words."""
    cleaned = "".join(c if (c.isalnum() or c.isspace()) else " " for c in str(title))
    return " ".join(cleaned.split())


def fetch(paper: dict, *, allow_network: bool = True) -> dict | None:
    """Return the cached/fetched OpenAlex search response for a paper, or None.

    Reads the write-once cache first; only hits the network if allowed and the
    cache is cold. A fetched 200 response is written to the cache before
    returning. Network/HTTP errors return None (a declared gap), never crash.
    """
    name = _cache_name(paper["id"])
    cached = raw.read(SOURCE, name)
    if cached is not None:
        return json.loads(cached)
    if not allow_network:
        return None

    terms = _search_terms(paper["canonical_title"])
    if not terms:
        return None
    # mailto puts us in OpenAlex's polite pool (higher free daily budget).
    query = {"filter": f"title.search:{terms}", "per-page": "5", "mailto": "office@apparens.nl"}
    url = f"{API}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None
    finally:
        time.sleep(_PACE_SECONDS)
    raw.write_once(SOURCE, name, body)
    return json.loads(body)


def _pick(paper: dict, response: dict) -> dict | None:
    """Choose the canonical OpenAlex record for a paper, or None if none clears the bar.

    OpenAlex frequently holds several records for one work (a preprint, a published
    version, and stub duplicates). Title overlap alone cannot tell them apart, and the
    stubs sit at zero citations. So among records that both clear the title threshold
    AND are within a year of ours (a same-title work from another era is excluded), we
    take the one that actually accumulated the citations: the canonical record. Ties
    break by title similarity then by a stable id, so the choice is deterministic.
    """
    results = (response or {}).get("results") or []
    our_year = paper.get("year")
    qualified: list[tuple[dict, float]] = []
    for r in results:
        sim = _overlap(paper["canonical_title"], r.get("display_name") or r.get("title"))
        if sim < _MIN_TITLE_OVERLAP:
            continue
        ry = r.get("publication_year")
        if our_year and ry and abs(ry - our_year) > 1:
            continue  # same title, different era: a different work
        qualified.append((r, sim))
    if not qualified:
        return None
    best, sim = max(
        qualified,
        key=lambda t: (t[0].get("cited_by_count") or 0, t[1], str(t[0].get("id") or "")),
    )
    best["_title_sim"] = sim
    return best


def _metric(paper, match, name, value, confidence):
    return {
        "work_id": paper["id"],
        "metric_name": name,
        "value": float(value),
        "source": "OpenAlex",
        "retrieved_at": RETRIEVED_AT,
        "confidence": confidence,
        "provenance_url": match.get("id", ""),
        "license_note": LICENSE_NOTE,
    }


def parse(paper: dict, response: dict | None) -> dict:
    """Derive metrics (or declared gaps) from a cached response.

    Returns {"metrics": [...], "gaps": [{metric, reason}, ...]}. Two independent
    signals come off the same matched OpenAlex record:
      * citation_count: all-time cited_by_count (scale of impact)
      * readership_persistence: the number of distinct years the work keeps being
        cited, a longevity proxy from counts_by_year. A work cited across many
        years scores higher than a one-year spike; this rewards enduring use, not
        recent volume. A fuller longevity proxy (holdings over time, edition
        count, continued availability) is a declared deferred enhancement.
    Never imputes a value (rule 8); a missing field is a gap, not a zero.
    """
    if response is None:
        return {"metrics": [], "gaps": [{"metric": "*", "reason": "no cached OpenAlex response (offline / not harvested)"}]}
    match = _pick(paper, response)
    if match is None:
        return {"metrics": [], "gaps": [{"metric": "*", "reason": "no OpenAlex result cleared the title-match threshold"}]}

    sim = match.get("_title_sim", 0.0)
    year_ok = (not paper.get("year")) or paper.get("year") == match.get("publication_year")
    base_conf = "high" if sim >= 0.85 and year_ok else "medium"

    metrics, gaps = [], []
    citations = match.get("cited_by_count")
    if not citations:  # None or 0
        # A zero is not a credible impact signal here: it means OpenAlex matched a
        # fresh or stub record it has not yet aggregated citations into. Publishing
        # "0 citations" for a paper that plainly has them would be a wrong number,
        # which the method treats as worse than an honest gap (rule 8 in spirit).
        gaps.append({"metric": "citation_count", "reason": "OpenAlex record carries no citations yet (fresh or unindexed); declared gap, not a zero"})
    else:
        metrics.append(_metric(paper, match, "citation_count", citations, base_conf))

    cby = match.get("counts_by_year")
    persistence = sum(1 for e in (cby or []) if (e.get("cited_by_count") or 0) > 0)
    if not persistence:
        gaps.append({"metric": "readership_persistence", "reason": "OpenAlex record has no year-by-year citations yet; declared gap, not a zero"})
    else:
        # Longevity proxy: distinct years in which the work kept being cited.
        # Derived proxy: one notch below the all-time count's confidence.
        conf = "medium" if base_conf == "high" else "low"
        metrics.append(_metric(paper, match, "readership_persistence", persistence, conf))

    return {"metrics": metrics, "gaps": gaps}


def harvest(limit: int | None = None, *, allow_network: bool = True) -> dict:
    """Populate the cache for papers and report coverage. Does not write metrics
    (assembly derives those from the cache)."""
    papers = load_papers()
    if limit:
        papers = papers[:limit]
    fetched = cached = gaps = 0
    for paper in papers:
        had_cache = raw.exists(SOURCE, _cache_name(paper["id"]))
        resp = fetch(paper, allow_network=allow_network)
        if resp is None:
            gaps += 1
            continue
        if had_cache:
            cached += 1
        else:
            fetched += 1
    report = {
        "papers_considered": len(papers),
        "newly_fetched": fetched,
        "served_from_cache": cached,
        "uncovered": gaps,
    }
    print(json.dumps(report, indent=2))
    return report


def _main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="OpenAlex harvester (papers)")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--offline", action="store_true", help="cache-only, no network")
    args = p.parse_args(argv)
    harvest(limit=args.limit, allow_network=not args.offline)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
