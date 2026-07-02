"""Stage C - static site generator (CAN-21..25).

Reads data/releases/<version>/ + data/seeds/ + scenarios.yaml + CHANGELOG.md and
emits plain, framework-free HTML into site/. The whole public site is generated
from the canonical JSON: there is no app server and no live database, so nothing
can leak or be injected (master doc, Part V). Output is deterministic.

The visual language mirrors apparens.nl (apparens-design-system.css): deep-blue
fixed nav with the white wordmark, white body, orange #B8430A accents, DM Serif
Display headings, DM Sans body. House style: no em-dashes in copy.

This module is the orchestrator and the public import surface; the renderers
live in canon.sitegen. Pages generated (17 top-level, all in the same design):
  index.html             the manifesto + the live Canon-50 teaser
  search.html            in-browser search over the whole corpus
  library.html           the candidate books, filterable, described
  canon-50.html          three scenario views; each rank links to its breakdown
  papers.html            all papers, honest about scored-vs-seed status
  frontier.html          the research frontier map, from the papers' own words
  models.html            models indexed to their paper; never a leaderboard
  voices.html            people in AI, described and never ranked
  organizations.html     organizations, described and never ranked
  platforms.html         platforms and tools, described and never ranked
  method.html            the 8 rules, ontology, weighting scenarios, missing-data rule
  challenges.html        the challenge protocol + log (the differentiator; empty for now)
  changelog.html         rendered from CHANGELOG.md
  data.html              the downloadable audit package + one-command reproduce
  about.html             the statement: why, what, how to read it
  press.html             the press and writers' guide
  share.html             ready-to-adapt sharing copy
  work/<id>.html         the per-work trust surface (every metric + provenance)
  audit/                 copied release + seed JSON (openly downloadable)
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

# Re-exported so `from canon import export_site as site` keeps its whole surface
# (tests and tools import every one of these through this module).
from .sitegen.assets_js import _LIB_FILTER_JS, _SEARCH_JS, _search_index_js  # noqa: F401
from .sitegen.common import (CONCEPT_DOI, DEFAULT_DESC, HUMILITY, PAGE_DESC,  # noqa: F401
                             POSITIONING, RELEASES, SEEDS, SITE, SITE_URL, VERSION,
                             _abs_source, _abstracts, _canonical_url, _load,
                             _papers_index, _ROOT, _scenarios, _write, _WRITTEN,
                             esc, esc_verbatim, safe_url)
from .sitegen.pages_context import page_frontier, page_orgs, page_platforms, page_voices  # noqa: F401
from .sitegen.pages_corpus import (_model_slug, _teaser_rows, page_canon50,  # noqa: F401
                                   page_home, page_library, page_models,
                                   page_papers, page_work)
from .sitegen.pages_meta import (_md_to_html, page_about, page_challenges,  # noqa: F401
                                 page_changelog, page_data, page_method,
                                 page_press, page_search, page_share)
from .sitegen.shell import GITHUB_REPO, NAV, SHARE_TEXT, SHARE_URL, _nav, share_row, shell  # noqa: F401
from .sitegen.theme import _HEADERS, _STYLE, JSONLD, JSONLD_HASH, _build_jsonld, _csp_hash  # noqa: F401


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    import csv
    import io

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(buf.getvalue(), encoding="utf-8")


def _write_assets() -> None:
    # Externalized assets so the CSP can forbid inline script and style entirely.
    _write("assets/canon.css", _STYLE.strip() + "\n")
    _write("assets/canon.js", _LIB_FILTER_JS.strip() + "\n")
    _write("_headers", _HEADERS)


def _gc_stale_work_pages(breakdowns: dict) -> None:
    # Clear stale work pages so a rebuild on changed evidence cannot leave an
    # orphaned "scored" page for a work that is now a declared gap.
    work_dir = SITE / "work"
    if work_dir.exists():
        keep = {f"{wid}.html" for wid in breakdowns}
        for stale in work_dir.glob("*.html"):
            if stale.name not in keep:
                stale.unlink()


def _write_pages(release, rankings, breakdowns, papers, scored, coverage,
                 books, persons, orgs, platforms) -> dict:
    """Write the 17 top-level pages and every work page. Returns the models
    index, which is read mid-sequence (kept exactly where it always was)."""
    _write("index.html", page_home(release, rankings, papers, coverage))
    _write("library.html", page_library(books))
    _write("canon-50.html", page_canon50(release, rankings, papers))
    _gc_stale_work_pages(breakdowns)
    for wid, per_scenario in breakdowns.items():
        _write(f"work/{wid}.html", page_work(wid, per_scenario, papers))
    _write("papers.html", page_papers(papers, scored))
    _write("frontier.html", page_frontier())
    models_index = _load(SEEDS.parent / "models_index.json")
    _write("models.html", page_models(models_index, papers, scored))
    _write("voices.html", page_voices(persons))
    _write("organizations.html", page_orgs(orgs))
    _write("platforms.html", page_platforms(platforms))
    _write("method.html", page_method())
    _write("challenges.html", page_challenges())
    _write("changelog.html", page_changelog())
    _write("data.html", page_data(release, coverage))
    _write("about.html", page_about())
    _write("press.html", page_press())
    _write("share.html", page_share())
    return models_index


def _write_search_index(books, papers, scored, persons, orgs, platforms, models_index) -> None:
    # Global search: an embedded index (so the strict CSP needs no connect-src) + a self script.
    _write("assets/search-index.js",
           _search_index_js(books, papers, scored, persons, orgs, platforms, models_index))
    _write("assets/search.js", _SEARCH_JS.strip() + "\n")
    _write("search.html", page_search())


def _copy_audit(books, papers) -> None:
    # Copy the audit package + open corpus so they are publicly downloadable.
    audit_rel = SITE / "audit" / VERSION
    if audit_rel.exists():
        shutil.rmtree(audit_rel)
    shutil.copytree(RELEASES / VERSION, audit_rel)
    seeds_out = SITE / "audit" / "seeds"
    seeds_out.mkdir(parents=True, exist_ok=True)
    for name in ("papers.json", "books.json", "persons.json", "orgs.json", "platforms.json"):
        shutil.copy(SEEDS / name, seeds_out / name)
    # Open CSV mirrors of the corpus (longevity / consumable without the site).
    _write_csv(seeds_out / "books.csv",
               ["id", "title", "author", "year", "language", "category", "source", "conflict_flag"],
               [[b["id"], b["canonical_title"], b["editorial"].get("author", ""), b.get("year", ""),
                 b.get("language", ""), b["editorial"].get("category", ""),
                 b["editorial"].get("source", ""), b["conflict_flag"]] for b in books])
    _write_csv(seeds_out / "papers.csv",
               ["id", "title", "authors", "year", "venue", "category"],
               [[p["id"], p["canonical_title"], p["editorial"].get("authors", ""), p.get("year", ""),
                 p["editorial"].get("venue", ""), p["editorial"].get("category", "")] for p in papers.values()])


def _write_seo(release: dict) -> None:
    # --- SEO: sitemap.xml, robots.txt, llms.txt ---
    lastmod = release.get("date", "")
    html_files = sorted(p for p in _WRITTEN if p.endswith(".html"))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for rel in html_files:
        sm.append(f"  <url><loc>{esc(_canonical_url(rel))}</loc>"
                  + (f"<lastmod>{esc(lastmod)}</lastmod>" if lastmod else "") + "</url>")
    sm.append("</urlset>")
    _write("sitemap.xml", "\n".join(sm) + "\n")

    # The Canon is a public-good, CC BY reference meant to be read and cited, by
    # people and by machines, so crawling is welcomed rather than fenced off.
    _write("robots.txt",
           "User-agent: *\nAllow: /\n\nSitemap: " + SITE_URL + "sitemap.xml\n")

    llms = (
        f"# The AI Canon\n\n"
        f"> {DEFAULT_DESC}\n\n"
        "The AI Canon is a free, public-good project by Apparens. It is reproducible and "
        "method-backed: every ranking links to its evidence, the corpus and weights are open, "
        "and anyone can challenge any entry. It ranks texts, not people, and it is built to "
        "include the Chinese-language literature in the core, not as a footnote.\n\n"
        "## Start here\n"
        f"- [The Canon 50]({SITE_URL}canon-50.html): AI papers ranked under three published weighting scenarios, each rank linking to its full evidence.\n"
        f"- [Method]({SITE_URL}method.html): how scoring works, the weights, and what is deliberately deferred or excluded.\n"
        f"- [About]({SITE_URL}about.html): what the Canon is and is not.\n\n"
        "## The corpus\n"
        f"- [Library]({SITE_URL}library.html): candidate books across every theme, each described, filterable by category, language, and provenance.\n"
        f"- [Papers]({SITE_URL}papers.html): seed papers from 1943 to 2025, including the Chinese-language research spine.\n"
        f"- [Models]({SITE_URL}models.html): notable AI models indexed to their paper in the Canon.\n"
        f"- [Voices]({SITE_URL}voices.html): people in AI, described and never ranked, each with a checkable source.\n"
        f"- [Organizations]({SITE_URL}organizations.html) and [Platforms]({SITE_URL}platforms.html): context, never ranked.\n\n"
        "## Data and integrity\n"
        f"- [Open data and audit]({SITE_URL}data.html): the full corpus, the weights, every per-work breakdown, and the one command that reproduces the release.\n"
        f"- [Challenge protocol]({SITE_URL}challenges.html): contest any ranking or omission with evidence; every challenge and resolution is logged.\n"
        f"- [Changelog]({SITE_URL}changelog.html): every release and correction, dated and public.\n\n"
        "## How to cite\n"
        "Cite the release version shown on each page and the Zenodo DOI 10.5281/zenodo.21042034. "
        "A rank is an output of declared evidence and weights at a release date, not a verdict on worth.\n"
    )
    _write("llms.txt", llms)


def build() -> dict:
    _WRITTEN.clear()  # idempotent across in-process rebuilds (tests)
    _write_assets()

    release = _load(RELEASES / VERSION / "release.json")
    # A release artifact never carries a space in its filename; skipping them
    # keeps cloud-sync duplicate copies ("paper-0001 2.json") from becoming pages.
    rankings = {
        p.stem: _load(p)
        for p in sorted((RELEASES / VERSION / "rankings").glob("*.json"))
        if " " not in p.name
    }
    breakdowns = {
        p.stem: _load(p)
        for p in sorted((RELEASES / VERSION / "breakdowns").glob("*.json"))
        if " " not in p.name
    }
    papers = _papers_index()
    scored = set(breakdowns)
    coverage = _load(RELEASES / VERSION / "coverage.json")
    books = _load(SEEDS / "books.json")
    persons = _load(SEEDS / "persons.json")
    orgs = _load(SEEDS / "orgs.json")
    platforms = _load(SEEDS / "platforms.json")

    models_index = _write_pages(release, rankings, breakdowns, papers, scored,
                                coverage, books, persons, orgs, platforms)
    _write_search_index(books, papers, scored, persons, orgs, platforms, models_index)
    _copy_audit(books, papers)
    _write_seo(release)

    summary = {"pages": 13 + len(breakdowns), "work_pages": len(breakdowns), "version": VERSION}
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    build()
