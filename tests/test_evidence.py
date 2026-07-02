"""[S17] Evidence currency: the validation registers cover the corpus as shipped,
published bios rest on checked sources, and every quoted abstract carries provenance.

These tests pin the *currency* of the trust surface: they fail when the corpus
grows past its registers, when a bio is published from an unchecked source, or
when a verbatim abstract loses its source or license note.
"""
from __future__ import annotations

import csv
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _load(p: Path):
    return json.loads(p.read_text("utf-8"))


def _rows(name: str) -> list[dict]:
    with (DATA / "validation" / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _fold(name: str) -> frozenset:
    """Diacritic- and punctuation-insensitive name token set. The register and the
    seeds spell names differently (François/Francois, Jürgen/Juergen, 'Andrew Yao /
    Yao Qizhi' vs 'Andrew Yao (Yao Qizhi)'), so we compare folded token sets."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    for a, b in (("ue", "u"), ("oe", "o"), ("ae", "a")):
        s = s.replace(a, b)
    return frozenset("".join(c if c.isalnum() else " " for c in s).split())


def _sig(tokens: frozenset) -> str:
    """Order- and hyphenation-insensitive character signature: 'Zhi-Hua Zhou' and
    'Zhou Zhihua' share one, distinct full names practically never do."""
    return "".join(sorted("".join(tokens)))


def _match(register: dict, name: str):
    key = _fold(name)
    if key in register:
        return register[key]
    for rkey, row in register.items():
        if rkey <= key or key <= rkey or _sig(rkey) == _sig(key):
            return row
    return None


def test_papers_register_covers_corpus():
    corpus = {p["id"] for p in _load(DATA / "seeds" / "papers.json")}
    register = {r["id"] for r in _rows("papers_reconciliation.csv")}
    assert register == corpus, (
        f"papers register out of date: {len(corpus - register)} unregistered, "
        f"{len(register - corpus)} stale"
    )


def test_books_register_covers_corpus():
    corpus = {b["id"] for b in _load(DATA / "seeds" / "books.json")}
    register = {r["id"] for r in _rows("books_reconciliation.csv")}
    assert register == corpus, (
        f"books register out of date: {len(corpus - register)} unregistered, "
        f"{len(register - corpus)} stale"
    )


def test_no_published_bio_without_checked_source():
    ok = {"VERIFIED", "CORRECTED", "SOURCE-UPGRADED"}
    register = {_fold(r["voice"]): r for r in _rows("voices_validation_register.csv")}
    missing, unchecked = [], []
    for p in _load(DATA / "seeds" / "persons.json"):
        if not p.get("bio"):
            continue
        row = _match(register, p["name"])
        if row is None:
            missing.append(p["name"])
        elif row["content_status"] not in ok:
            unchecked.append((p["name"], row["content_status"]))
    assert not missing, f"{len(missing)} voices with a published bio but no register row: {missing[:5]}"
    assert not unchecked, f"published bios on unchecked sources: {unchecked[:5]}"


def test_every_abstract_carries_provenance():
    for pid, ab in _load(DATA / "abstracts.json").items():
        assert ab.get("text"), f"{pid}: empty abstract"
        assert ab.get("source"), f"{pid}: no source label"
        assert ab.get("retrieved"), f"{pid}: no retrieved date"
        assert ab.get("license_note"), f"{pid}: no license note"
        assert ab.get("source_url") or ab.get("source_url_note"), (
            f"{pid}: neither a source_url nor a declared source_url gap"
        )


def test_license_carveout_for_abstracts_present():
    text = (ROOT / "LICENSE-DATA").read_text("utf-8")
    assert "abstracts" in text and "NOT covered" in text, (
        "LICENSE-DATA lost the verbatim-abstracts carve-out"
    )
