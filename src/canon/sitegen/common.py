"""Shared paths, constants, escaping, and load/write helpers for the site generator."""

from __future__ import annotations

import html
import json
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[3]
SITE = _ROOT / "site"
SEEDS = _ROOT / "data" / "seeds"
RELEASES = _ROOT / "data" / "releases"
from .. import RELEASE_VERSION as VERSION  # single source (canon/__init__.py)

# The verbatim positioning line (A2) and humility clause (E5), used as-is.
CONCEPT_DOI = "10.5281/zenodo.21042034"  # always resolves to the latest method version
POSITIONING = ("The AI Canon is a free, method-backed reference library for AI "
               "knowledge. It ranks texts, not people. It invites correction. It sells nothing.")
HUMILITY = ("A rank is not a verdict on intrinsic worth. It is a transparent output of "
            "declared evidence, weights, and missing-data rules at a specific release date.")

# --- SEO: canonical site URL, per-page descriptions, and structured data ---
SITE_URL = "https://ai-canon.apparens.nl/"
DEFAULT_DESC = ("The AI Canon is a free, method-backed, reproducible reference library for "
                "artificial intelligence. It ranks texts, not people, and shows the evidence behind every rank.")

_COUNTS_CACHE: dict | None = None


def counts() -> dict:
    """Corpus counts computed from the seed data, the single source, so page
    copy can never drift from the corpus again (they used to be hand-typed)."""
    global _COUNTS_CACHE
    if _COUNTS_CACHE is None:
        def n(name):
            return len(json.loads((SEEDS / name).read_text("utf-8")))
        _COUNTS_CACHE = {
            "books": n("books.json"), "papers": n("papers.json"),
            "voices": n("persons.json"), "orgs": n("orgs.json"),
            "platforms": n("platforms.json"),
            "models": len(json.loads((SEEDS.parent / "models_index.json").read_text("utf-8"))["models"]),
        }
    return _COUNTS_CACHE


# Per-page meta descriptions, keyed by the page's own path. Pages not listed fall
# back to DEFAULT_DESC; work pages pass their own description. Each is a distinct,
# honest summary (no two pages share a description, which search engines reward).
PAGE_DESC = {
    "index.html": DEFAULT_DESC,
    "canon-50.html": "The Canon 50: AI papers ranked under three published weighting scenarios, each rank linking to its full evidence. A pilot release, honest about its scope.",
    "library.html": f"Browse {counts()['books']} candidate AI books across every theme, filterable by category, language, and provenance. Curated and described, labelled candidacy, not canon.",
    "papers.html": f"All {counts()['papers']} AI papers from 1943 to 2026: the seed corpus plus recent work surfaced by the frontier review, including the Chinese-language research spine. Each scored paper links to its harvested evidence.",
    "frontier.html": "What the canon's papers say they have not solved: their stated open problems pooled, coded, and adversarially audited into a map of research frontiers, traceable to the papers' own words.",
    "models.html": f"An index of {counts()['models']} notable AI models, each linked to its paper in the Canon and to its own model page. A way into the literature, never a leaderboard.",
    "voices.html": f"{counts()['voices']} voices in artificial intelligence, described and never ranked, each with a checkable source. The Canon ranks texts, not people.",
    "organizations.html": "The organizations shaping artificial intelligence, each described with a link to learn more. Context for the Canon, never ranked.",
    "platforms.html": "The platforms and tools of artificial intelligence, described and linked. Context for the Canon, never ranked.",
    "method.html": "How the AI Canon is built: a deterministic, reproducible scoring method with published weights, declared evidence, and no imputed numbers.",
    "challenges.html": "Challenge any ranking or omission in the AI Canon with evidence. Every challenge and its resolution is published in a permanent, public log.",
    "changelog.html": "The append-only changelog of the AI Canon: every release, every scoring change, and every correction, dated and public.",
    "data.html": "Download the AI Canon as open data: the full corpus, the weights, every per-work breakdown, and the one command that reproduces the release.",
    "about.html": "The AI Canon is a public research initiative by Apparens. Free, checkable, and built to include the Chinese-language literature in the core, not as a footnote.",
    "press.html": "A press and writers' guide to the AI Canon: what it is, what it is not, and how to cite it.",
    "share.html": "Share the AI Canon, a free reference library for AI knowledge that ranks texts, not people.",
    "search.html": "Search the whole AI Canon corpus: books, papers, models, voices, organizations, and platforms. The search runs entirely in your browser.",
}


def _canonical_url(path: str) -> str:
    return SITE_URL + ("" if path == "index.html" else path)


def esc(x) -> str:
    # House style: no em-dashes in copy. Normalize at the rendering boundary so
    # even verbatim seed text (descriptions, significance lines) cannot show one.
    # html.escape(quote=True) neutralizes < > & " ' so no data field can break out
    # of text or an attribute (XSS defense in depth).
    text = html.escape(str(x if x is not None else ""), quote=True)
    return text.replace(" — ", ", ").replace("—", ", ").replace("–", "-")


def esc_verbatim(x) -> str:
    """HTML-escape WITHOUT house-style dash rewriting. For quoted verbatim text
    only (abstracts, the frontier's verbatim quotes): the site promises the
    authors' own words, so an em-dash in a quote must survive to the page.
    The [S3] no-em-dash rule applies to generated copy, not to quotations."""
    return html.escape(str(x if x is not None else ""), quote=True)


# Only these URL schemes may appear in a generated href/src; anything else
# (javascript:, data:, vbscript:, file:, ...) collapses to "#". Defense in depth:
# a data-derived link (e.g. a metric's provenance_url) cannot become script.
_SAFE_SCHEMES = ("https://", "http://", "mailto:")


def safe_url(u) -> str:
    s = str(u or "").strip()
    if s.lower().startswith(_SAFE_SCHEMES):
        return s
    # Allow purely relative links (no scheme); reject any colon before the first
    # slash, which signals a scheme that is not on the allow-list.
    if ":" not in s.split("/", 1)[0]:
        return s
    return "#"


# Every page the builder writes, recorded so published artifacts (sitemap) are
# derived from what the build PRODUCED, never from a directory listing: a glob
# can pick up environment junk (e.g. iCloud " 2.html" duplicate copies).
_WRITTEN: set[str] = set()


def _write(rel_path: str, content: str) -> None:
    _WRITTEN.add(rel_path)
    out = SITE / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


def _load(path: Path):
    return json.loads(path.read_text("utf-8"))


def _papers_index() -> dict:
    return {p["id"]: p for p in _load(SEEDS / "papers.json")}


def _scenarios() -> dict:
    return yaml.safe_load((_ROOT / "scenarios.yaml").read_text("utf-8"))


_ABSTRACTS_CACHE = None


def _abstracts() -> dict:
    """paper_id -> {text, source}. Loaded once; the file is optional (missing -> no abstracts)."""
    global _ABSTRACTS_CACHE
    if _ABSTRACTS_CACHE is None:
        path = SEEDS.parent / "abstracts.json"
        _ABSTRACTS_CACHE = _load(path) if path.exists() else {}
    return _ABSTRACTS_CACHE


def _abs_source(ab: dict) -> str:
    """The provenance tail of a rendered abstract: linked when the entry carries
    a checkable source_url, plain label when it does not (a declared gap)."""
    label = esc(ab.get("source", ""))
    url = ab.get("source_url", "")
    if url:
        return (f'<span class="asrc"> [<a href="{esc(safe_url(url))}" target="_blank" '
                f'rel="noopener noreferrer">{label}</a>]</span>')
    return f'<span class="asrc"> [{label}]</span>'
