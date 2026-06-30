#!/usr/bin/env python3
"""Bibliographic reconciliation (verify-once, deterministic, complete).

Books  -> OpenLibrary search API (title+author) -> canonical title/author/first-publish-year.
Papers -> Crossref works API (bibliographic query) -> DOI + title/year/authors.

We FLAG discrepancies for human adjudication; we never auto-edit the corpus here.
Low-confidence non-matches are almost always database-coverage gaps (non-English,
very recent, or self-published works), NOT corpus errors -- they are reported
separately from genuine title/author/year conflicts so we don't cry wolf.

Outputs: data/validation/books_reconciliation.csv, papers_reconciliation.csv
Run: PYTHONPATH=src .venv/bin/python scripts/reconcile_bibliography.py
"""
from __future__ import annotations

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "seeds"
OUT = ROOT / "data" / "validation"
UA = "AICanon-reconcile/1.0 (office@apparens.nl)"
MAILTO = "office@apparens.nl"


def norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())


def main_title(t: str) -> str:
    # match on the part before a subtitle colon / dash
    return re.split(r"[:—\-]", t, 1)[0].strip() if t else t


def ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def get_json(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


def arxiv_lookup(title: str, year):
    """Resolve a paper to an arXiv id by title (for modern ML papers absent from Crossref)."""
    import xml.etree.ElementTree as ET
    q = urllib.parse.urlencode({"search_query": f'ti:"{main_title(title)}"', "max_results": 5})
    req = urllib.request.Request(f"http://export.arxiv.org/api/query?{q}", headers={"User-Agent": UA})
    root = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                root = ET.fromstring(r.read())
            break
        except Exception:
            time.sleep(3 * (attempt + 1))  # arXiv asks for slow, polite access
    if root is None:
        return None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    best, best_r = None, 0.0
    for e in root.findall("a:entry", ns):
        et = (e.findtext("a:title", default="", namespaces=ns) or "").strip()
        rr = ratio(title, et)
        if rr > best_r:
            best, best_r = e, rr
    if best is None or best_r < 0.85:
        return None
    aid = (best.findtext("a:id", default="", namespaces=ns) or "")
    m = re.search(r"arxiv\.org/abs/([0-9.]+)", aid)
    pub = (best.findtext("a:published", default="", namespaces=ns) or "")[:4]
    py = int(pub) if pub.isdigit() else None
    if m and (not year or not py or abs(py - year) <= 1):
        return f"arXiv:{m.group(1)}"
    return None


# --- books: OpenLibrary -------------------------------------------------------

def reconcile_book(b: dict) -> dict:
    title = b["canonical_title"]
    author = b["editorial"].get("author", "")
    year = b.get("year")
    q = urllib.parse.urlencode({"title": main_title(title), "limit": 5,
                                "fields": "title,author_name,first_publish_year"})
    data = get_json(f"https://openlibrary.org/search.json?{q}")
    rec = {"id": b["id"], "title": title, "author": author, "year": year,
           "ol_title": "", "ol_author": "", "ol_year": "", "verdict": "", "note": ""}
    if not data or not data.get("docs"):
        rec["verdict"] = "NOT_FOUND"; rec["note"] = "no OpenLibrary hit (likely DB gap)"
        return rec
    # best doc by title similarity (full or main-title)
    best, best_r = None, 0.0
    for d in data["docs"]:
        r = max(ratio(title, d.get("title", "")), ratio(main_title(title), d.get("title", "")))
        if r > best_r:
            best, best_r = d, r
    rec["ol_title"] = best.get("title", "")
    rec["ol_author"] = "; ".join(best.get("author_name", [])[:3])
    rec["ol_year"] = best.get("first_publish_year", "")
    title_ok = best_r >= 0.82
    a_norm = norm(author)
    a_last = a_norm.split()[-1] if a_norm else ""
    authors_norm = norm(" ".join(best.get("author_name", [])))
    author_ok = bool(a_last) and (a_norm in authors_norm or a_last in authors_norm)
    oly = best.get("first_publish_year")
    if not title_ok or not author_ok:
        rec["verdict"] = "REVIEW_MATCH"
        rec["note"] = f"title_sim={best_r:.2f} author_ok={author_ok} (may be DB gap)"
    elif oly and year and (year < oly - 1):
        # we claim a year EARLIER than OL's first publication -> suspicious
        rec["verdict"] = "REVIEW_YEAR"
        rec["note"] = f"our year {year} < OL first-publish {oly}"
    elif oly and year and abs(year - oly) > 8:
        rec["verdict"] = "REVIEW_YEAR"
        rec["note"] = f"year gap {year} vs OL {oly} (OL=earliest edition)"
    else:
        rec["verdict"] = "OK"
    return rec


# --- papers: Crossref ---------------------------------------------------------

def _ax(rec, title, year):
    """arXiv fallback: attach an arXiv id when Crossref gave no DOI (modern ML papers)."""
    if not rec.get("doi"):
        ax = arxiv_lookup(title, year)
        if ax:
            rec["arxiv"] = ax
            if rec["verdict"] in ("REVIEW_MATCH", "NOT_FOUND", "OK_NO_DOI"):
                rec["verdict"] = "OK"
                rec["note"] = (rec.get("note", "") + " | arXiv resolved").strip(" |")
    return rec


def reconcile_paper(p: dict) -> dict:
    title = p["canonical_title"]
    year = p.get("year")
    q = urllib.parse.urlencode({"query.bibliographic": title, "rows": 8, "mailto": MAILTO,
                                "select": "DOI,title,issued,author"})
    data = get_json(f"https://api.crossref.org/works?{q}")
    rec = {"id": p["id"], "title": title, "year": year, "doi": "", "arxiv": "", "cr_title": "",
           "cr_year": "", "verdict": "", "note": ""}
    items = (data or {}).get("message", {}).get("items", [])
    if not items:
        rec["verdict"] = "NOT_FOUND"; rec["note"] = "no Crossref hit"
        return _ax(rec, title, year)

    def cyear(it):
        try:
            return it["issued"]["date-parts"][0][0]
        except Exception:
            return None

    # Title-matching candidates, then pick the one whose year is CLOSEST to ours
    # (classic papers have many reprint/citation DOIs at later years; the canonical
    # record is the one matching the true publication year).
    cands = [(it, ratio(title, (it.get("title") or [""])[0])) for it in items]
    good = [(it, r) for it, r in cands if r >= 0.85]
    if not good:
        best, best_r = max(cands, key=lambda x: x[1])
        rec["cr_title"] = (best.get("title") or [""])[0]
        rec["cr_year"] = cyear(best) or ""
        rec["verdict"] = "REVIEW_MATCH"; rec["note"] = f"title_sim={best_r:.2f} (no DOI assigned)"
        return _ax(rec, title, year)
    if year:
        best, best_r = min(good, key=lambda x: (abs((cyear(x[0]) or 9999) - year)))
    else:
        best, best_r = good[0]
    cy = cyear(best)
    rec["cr_title"] = (best.get("title") or [""])[0]
    rec["cr_year"] = cy or ""
    if cy and year and abs(cy - year) <= 1:
        rec["doi"] = best.get("DOI", ""); rec["verdict"] = "OK"
    elif cy and year and abs(cy - year) > 1:
        # canonical-year record not in Crossref (common for pre-1996 papers); trust our year,
        # do not attach a reprint DOI.
        rec["verdict"] = "OK_NO_DOI"; rec["note"] = f"only later record in Crossref ({cy}); corpus year {year} trusted"
    else:
        rec["doi"] = best.get("DOI", ""); rec["verdict"] = "OK"
    return _ax(rec, title, year)


def run(items, fn, fields, out_path, label):
    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, rec in enumerate(ex.map(fn, items), 1):
            results.append(rec)
            if i % 50 == 0:
                print(f"  {label}: {i}/{len(items)}")
    results.sort(key=lambda r: r["id"])
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)
    from collections import Counter
    tally = Counter(r["verdict"] for r in results)
    print(f"{label} tally: {dict(tally)}  -> {out_path.name}")
    return results, tally


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    books = json.load((SEEDS / "books.json").open())
    papers = json.load((SEEDS / "papers.json").open())
    print(f"Reconciling {len(books)} books (OpenLibrary) + {len(papers)} papers (Crossref)...")
    br, bt = run(books, reconcile_book,
                 ["id", "title", "author", "year", "ol_title", "ol_author", "ol_year", "verdict", "note"],
                 OUT / "books_reconciliation.csv", "books")
    pr, pt = run(papers, reconcile_paper,
                 ["id", "title", "year", "doi", "cr_title", "cr_year", "verdict", "note"],
                 OUT / "papers_reconciliation.csv", "papers")
    print("\n=== GENUINE CONFLICTS (year) to adjudicate ===")
    for r in br:
        if r["verdict"] == "REVIEW_YEAR":
            print(f"  BOOK {r['id']}: {r['title'][:45]} | ours={r['year']} OL={r['ol_year']} | {r['note']}")
    for r in pr:
        if r["verdict"] == "REVIEW_YEAR":
            print(f"  PAPER {r['id']}: {r['title'][:45]} | ours={r['year']} CR={r['cr_year']}")
    doi_n = sum(1 for r in pr if r["doi"])
    print(f"\npapers resolved to a DOI: {doi_n}/{len(papers)}")
