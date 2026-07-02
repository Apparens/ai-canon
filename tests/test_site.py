"""Stage C — static site generation smoke tests (CAN-21..25)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from canon import export_site as site

_REL = Path(__file__).resolve().parents[1] / "data" / "releases" / site.VERSION

pytestmark = pytest.mark.skipif(
    not (_REL / "release.json").exists(), reason="no release — run `make release` first"
)


def test_build_emits_home_core_and_work_pages():
    summary = site.build()
    for name in ("index.html", "canon-50.html", "papers.html", "method.html",
                 "challenges.html", "changelog.html", "data.html"):
        assert (site.SITE / name).exists(), name
    assert summary["work_pages"] > 0


def test_no_broken_internal_links():
    site.build()
    broken = []
    for html in site.SITE.rglob("*.html"):
        for href in re.findall(r'href="([^"]+)"', html.read_text("utf-8")):
            if href.startswith(("http", "mailto:", "#")):
                continue
            path = href.split("#")[0].split("?")[0]
            if not path:
                continue
            target = (html.parent / path).resolve()
            # Cloudflare Pages has no directory listing: a dir link only works if
            # it has an index.html, otherwise it 403/404s. Require a real file.
            ok = (target / "index.html").exists() if target.is_dir() else target.exists()
            if not ok:
                broken.append((html.name, href))
    assert broken == [], broken[:10]


def test_home_is_generated_with_live_teaser():
    site.build()
    home = (site.SITE / "index.html").read_text("utf-8")
    # The homepage is generated in the shared design and links a real work page.
    assert re.search(r'work/paper-\d+\.html', home)
    assert 'class="brandwrap"' in home  # the apparens-style nav


def test_voice_bio_renders_only_when_present():
    with_bio = site.page_voices([{"id": "person-x", "name": "Test Voice", "category": "X",
                                  "known_for": "known for line", "bio": "An authored biography sentence.",
                                  "region": "NL"}])
    assert "An authored biography sentence." in with_bio and 'class="bio"' in with_bio
    without = site.page_voices([{"id": "person-y", "name": "No Bio", "category": "X",
                                 "known_for": "kf", "region": "NL"}])
    assert 'class="bio"' not in without  # quiet when no bio is written


def test_voice_source_link_renders_and_is_safe():
    html = site.page_voices([{"id": "person-z", "name": "Sourced Voice", "category": "X",
                              "source_url": "https://example.org/profile", "region": "NL"}])
    assert 'class="src"' in html and "https://example.org/profile" in html
    # A non-http(s) scheme must be neutralised by safe_url, never emitted raw.
    bad = site.page_voices([{"id": "person-b", "name": "Bad", "source_url": "javascript:alert(1)"}])
    assert "javascript:alert" not in bad


def test_no_self_referential_voice_sources():
    """[integrity] The Canon must never cite itself to validate an entry."""
    import json
    persons = json.loads((_REL.parents[2] / "data" / "seeds" / "persons.json").read_text("utf-8"))
    offenders = [p["name"] for p in persons if "ai-canon.apparens.nl" in (p.get("source_url") or "")]
    assert offenders == [], offenders


_VERBATIM_BLOCKS = re.compile(
    r'<details class="abs"[^>]*>.*?</details>|<ul class="fq">.*?</ul>', re.S)


def test_no_em_dashes_in_generated_copy():
    """[S3] House style bans em-dashes in GENERATED copy. Verbatim quotations
    (abstracts, the frontier's verbatim quotes) are the authors' own words and
    are exempt: mutating a quote would break the site's verbatim promise."""
    site.build()
    offenders = [h.name for h in site.SITE.rglob("*.html")
                 if "—" in _VERBATIM_BLOCKS.sub("", h.read_text("utf-8"))]
    assert offenders == [], offenders


def test_verbatim_quotes_keep_their_em_dashes():
    """The inverse guarantee: a verbatim abstract that contains an em-dash must
    reach the page intact (ELIZA's abstract famously opens with one)."""
    import json
    ab = json.loads((site.SEEDS.parent / "abstracts.json").read_text("utf-8"))
    dash_papers = [pid for pid, e in ab.items() if "—" in e["text"]]
    if not dash_papers:
        pytest.skip("no stored abstract currently contains an em-dash")
    site.build()
    papers_html = (site.SITE / "papers.html").read_text("utf-8")
    assert "—" in papers_html, "em-dash in a verbatim abstract was mangled at render"


def test_accessibility_invariants():
    """[S13] Static a11y guardrail. The full Axe pass is clean; this keeps the
    structural prerequisites from regressing without a browser in CI: a language,
    exactly one h1, alt text on every image, and no skipped heading levels."""
    site.build()
    problems = []
    for html in site.SITE.rglob("*.html"):
        t = html.read_text("utf-8")
        if '<html lang="' not in t:
            problems.append(f"{html.name}: missing lang")
        if t.count("<h1") != 1:
            problems.append(f"{html.name}: {t.count('<h1')} h1 (want 1)")
        for img in re.findall(r"<img\b[^>]*>", t):
            if "alt=" not in img:
                problems.append(f"{html.name}: img without alt")
        levels = [int(m) for m in re.findall(r"<h([1-6])\b", t)]
        for prev, cur in zip(levels, levels[1:]):
            if cur > prev + 1:
                problems.append(f"{html.name}: heading jump h{prev}->h{cur}")
                break
    assert problems == [], problems
