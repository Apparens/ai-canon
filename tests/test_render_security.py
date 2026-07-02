"""[S18] Hostile-fixture render tests: every data field that reaches HTML is
injected with attack strings and the output is asserted breakout-free.

These complement test_security.py (which checks the REAL site output): here the
inputs are adversarial, so a renderer that forgets esc()/safe_url() on any
data-derived field fails immediately, not when hostile data arrives.
"""
from __future__ import annotations

import pytest

from canon import export_site as site
from canon import raw
from canon.sitegen import pages_corpus

HOSTILE = '"><script>alert(1)</script><b x="'
HOSTILE_URL = 'https://example.com/"onmouseover="alert(1)'
JS_URL = "javascript:alert(1)"


def _assert_contained(html: str, context: str):
    assert "<script>alert" not in html, f"script breakout in {context}"
    assert 'onmouseover="alert' not in html, f"attribute breakout in {context}"
    assert 'href="javascript:' not in html.lower(), f"javascript: href in {context}"


def test_work_page_contains_hostile_fields():
    papers = {"paper-x": {
        "canonical_title": HOSTILE, "year": HOSTILE, "conflict_flag": True,
        "editorial": {"authors": HOSTILE, "significance": HOSTILE, "venue": HOSTILE},
    }}
    per_scenario = {"academic": {
        "score": 1.0, "rank": 1, "work_id": "paper-x", "work_type": "paper",
        "components": [
            {"metric": HOSTILE, "status": "present", "value": HOSTILE,
             "normalized": 1, "weight": 1, "contribution": 1, "source": HOSTILE,
             "confidence": HOSTILE, "provenance_url": JS_URL},
            {"metric": HOSTILE, "status": "missing",
             "missing_data_penalty": HOSTILE, "note": HOSTILE},
        ],
    }}
    html = site.page_work("paper-x", per_scenario, papers)
    _assert_contained(html, "page_work")


def test_papers_page_contains_hostile_fields(monkeypatch):
    # page_papers resolves _load in its own module, so patch it where it looks.
    monkeypatch.setattr(pages_corpus, "_load", lambda p: {"paper-x": {
        "text": HOSTILE, "source": HOSTILE, "source_url": HOSTILE_URL}})
    papers = {"paper-x": {
        "canonical_title": HOSTILE, "year": HOSTILE,
        "editorial": {"significance": HOSTILE, "venue": HOSTILE},
    }}
    html = site.page_papers(papers, {"paper-x"})
    _assert_contained(html, "page_papers")


def test_context_pages_contain_hostile_fields():
    person = {"name": HOSTILE, "bio": HOSTILE, "anchor_affiliation": HOSTILE,
              "known_for": HOSTILE, "category": HOSTILE, "region": HOSTILE,
              "source_url": HOSTILE_URL, "id": "person-x", "canonical": False}
    html = site.page_voices([person])
    _assert_contained(html, "page_voices")
    assert 'href="https://example.com/' in html  # link survives, quote does not break out


def test_models_page_contains_hostile_fields():
    midx = {"note": HOSTILE, "as_of": HOSTILE, "epoch_url": JS_URL,
            "models": [{"name": HOSTILE, "lab": HOSTILE, "country": HOSTILE,
                        "paper": "", "ext": HOSTILE_URL}]}
    html = site.page_models(midx, {}, set())
    _assert_contained(html, "page_models")
    assert 'href="#"' in html  # javascript: epoch_url collapsed by safe_url


def test_shell_contains_hostile_title_without_double_escape():
    html = site.shell("papers.html", "K", 'A & B "quoted" <title>', "<p>body</p>")
    assert "&amp;amp;" not in html, "double-escaped title"
    assert "<title>A &amp; B" in html


def test_safe_url_wrapped_in_esc_everywhere():
    """A safe_url() result interpolated into href= must also be esc()'d: safe_url
    passes quotes through by design. Grep the generator for regressions."""
    from pathlib import Path
    sources = [Path(site.__file__)] + sorted(Path(pages_corpus.__file__).parent.glob("*.py"))
    for f in sources:
        assert 'href="{safe_url' not in f.read_text(), f"bare safe_url in an href attribute in {f.name}"


def test_raw_read_raises_on_tampered_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(raw, "RAW_DIR", tmp_path)
    raw.write_once("src", "rec.json", b'{"a":1}')
    (tmp_path / "src" / "rec.json").write_bytes(b'{"a":2}')  # tamper post-write
    with pytest.raises(raw.RawIntegrityError):
        raw.read("src", "rec.json")


def test_raw_path_rejects_traversal():
    for bad in ("../x", "a/b", "..", ".hidden/../x", "a b"):
        with pytest.raises(ValueError):
            raw.raw_path("openalex", bad)
