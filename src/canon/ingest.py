"""CAN-07 — import the three seed workbooks into schema-valid JSON.

Every row is validated against schema.py before it is written. Counts are
asserted hard (610 / 226 / 184 / 133 / 90). Editorial metadata about a book's
description (DescConfidence, Source, Description) is kept verbatim but stored
in an `editorial` block — it is NOT canonical evidence (master doc: DescConfidence
is confidence in the description, not in any ranking signal).

`authored_by` edges are derived by full-name containment of a curated voice's
name inside a work's author string (NFC + casefold). Expect ~168 (+/-10%); a
count outside that band is printed as a warning to investigate, never silently
accepted and never silently "fixed".

Output is deterministic: stable ids from the source row order, sorted JSON keys,
trailing newline. Re-running on the same workbooks produces byte-identical files.
"""

from __future__ import annotations

import json
import unicodedata
from datetime import date
from pathlib import Path

import openpyxl

from .schema import Edge, Organization, Person, Platform, Work

_REPO_ROOT = Path(__file__).resolve().parents[2]
SEEDS_DIR = _REPO_ROOT / "data" / "seeds"

# Source workbooks live alongside the repo for the pilot import.
SOURCE_DIR = Path.home() / "Desktop" / "files"
BOOKS_XLSX = SOURCE_DIR / "AI_Canon_SeedCorpus_v03.xlsx"
PAPERS_XLSX = SOURCE_DIR / "AI_Canon_Papers_Seed.xlsx"
CONTEXT_XLSX = SOURCE_DIR / "AI_Canon_Voices_Orgs_Platforms.xlsx"

SEED_DATE = date(2026, 6, 14)  # seed v0.3 (changelog)
APPARENS_CONFLICT_TITLE = "the ai accountability trap"  # rule 12

EXPECTED = {"books": 610, "papers": 226, "persons": 184, "orgs": 133, "platforms": 90}
AUTHORED_BY_BAND = (151, 185)  # ~168 +/-10%


def _norm(text) -> str:
    if text is None:
        return ""
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


def _year(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(str(value).strip()[:4])
    except (ValueError, IndexError):
        return None


def _rows(path: Path, sheet: str | None = None):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(it)]
    for row in it:
        if row is None or all(c is None or str(c).strip() == "" for c in row):
            continue
        yield dict(zip(header, row))
    wb.close()


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


# --- importers --------------------------------------------------------------


def import_books() -> tuple[list[dict], list[dict]]:
    """Return (book_records, categorized_as_edges)."""
    records: list[dict] = []
    edges: list[dict] = []
    for r in _rows(BOOKS_XLSX, "SeedCorpus"):
        nr = int(str(r["Nr"]).strip())
        wid = f"book-{nr:04d}"
        title = str(r["Title"]).strip()
        work = Work(
            id=wid,
            canonical_title=title,
            language=(str(r.get("Lang") or "").strip() or "und"),
            year=_year(r.get("Year")),
            work_type="book",
            conflict_flag=_norm(title) == APPARENS_CONFLICT_TITLE,
        )
        author = str(r.get("Author") or "").strip()
        category = str(r.get("Category") or "").strip()
        rec = work.model_dump(mode="json")
        rec["editorial"] = {
            "author": author,
            "category": category,
            "desc_confidence": str(r.get("DescConfidence") or "").strip(),
            "source": str(r.get("Source") or "").strip(),
            "description": (str(r["Description"]).strip() if r.get("Description") else ""),
        }
        records.append(rec)
        if category:
            edges.append(
                Edge(
                    from_id=wid,
                    to_id=f"category:{category}",
                    edge_type="categorized_as",
                    source=BOOKS_XLSX.name,
                    derivation_method="Category column (single tag; model supports many)",
                    last_verified=SEED_DATE,
                ).model_dump(mode="json")
            )
    return records, edges


def import_papers() -> list[dict]:
    records: list[dict] = []
    for r in _rows(PAPERS_XLSX):
        num = int(str(r["#"]).strip())
        wid = f"paper-{num:04d}"
        # Lang defaults to English (the seed papers are English); a non-empty Lang
        # column lets a Chinese-language paper enter as a work in its own ecosystem.
        work = Work(
            id=wid,
            canonical_title=str(r["Title"]).strip(),
            language=(str(r.get("Lang") or "").strip().lower() or "en"),
            year=_year(r.get("Year")),
            work_type="paper",
        )
        rec = work.model_dump(mode="json")
        rec["editorial"] = {
            "authors": str(r.get("Authors") or "").strip(),
            "venue": str(r.get("Venue") or "").strip(),
            "category": str(r.get("Category") or "").strip(),
            "confidence": str(r.get("Confidence") or "").strip(),
            "significance": str(r.get("Significance") or "").strip(),
            "source": str(r.get("Source") or "").strip(),
        }
        records.append(rec)
    return records


def import_persons() -> list[dict]:
    records: list[dict] = []
    for i, r in enumerate(_rows(CONTEXT_XLSX, "Voices"), start=1):
        person = Person(
            name=str(r["Name"]).strip(),
            category=str(r.get("Category") or "").strip() or None,
            known_for=str(r.get("Known for") or "").strip() or None,
            bio=str(r.get("Bio") or "").strip() or None,
            source_url=str(r.get("Source") or "").strip() or None,
            anchor_affiliation=str(
                r.get("Anchor / affiliation (verify before publish)") or ""
            ).strip()
            or None,
            region=str(r.get("Region") or "").strip() or None,
            last_verified=SEED_DATE,
        )
        rec = person.model_dump(mode="json")
        rec["id"] = f"person-{i:04d}"
        records.append(rec)
    return records


def import_orgs() -> list[dict]:
    records: list[dict] = []
    for i, r in enumerate(_rows(CONTEXT_XLSX, "Organizations"), start=1):
        org = Organization(
            name=str(r["Name"]).strip(),
            category=str(r.get("Category") or "").strip() or None,
            what_it_is=str(r.get("What it is") or "").strip() or None,
            source_url=str(r.get("Source") or "").strip() or None,
            region=str(r.get("Region") or "").strip() or None,
            last_verified=SEED_DATE,
        )
        rec = org.model_dump(mode="json")
        rec["id"] = f"org-{i:04d}"
        records.append(rec)
    return records


def import_platforms() -> list[dict]:
    records: list[dict] = []
    for i, r in enumerate(_rows(CONTEXT_XLSX, "Platforms"), start=1):
        plat = Platform(
            name=str(r["Name"]).strip(),
            category=str(r.get("Category") or "").strip() or None,
            what_it_is=str(r.get("What it is") or "").strip() or None,
            source_url=str(r.get("Source") or "").strip() or None,
            status=str(r.get("Status") or "").strip() or None,
            last_verified=SEED_DATE,
        )
        rec = plat.model_dump(mode="json")
        rec["id"] = f"platform-{i:04d}"
        records.append(rec)
    return records


def derive_authored_by(
    works: list[dict], persons: list[dict], author_key
) -> list[dict]:
    """Full-name containment of a voice's name inside a work's author string."""
    edges: list[dict] = []
    norm_persons = [(p["id"], _norm(p["name"]), p["name"]) for p in persons]
    for w in works:
        author_str = _norm(author_key(w))
        if not author_str:
            continue
        for pid, pname_norm, _ in norm_persons:
            if pname_norm and pname_norm in author_str:
                edges.append(
                    Edge(
                        from_id=w["id"],
                        to_id=pid,
                        edge_type="authored_by",
                        source="derived",
                        derivation_method="full-name containment (NFC+casefold) vs Voices seed",
                        last_verified=SEED_DATE,
                    ).model_dump(mode="json")
                )
    return edges


# --- orchestration ----------------------------------------------------------


def run() -> dict:
    books, cat_edges = import_books()
    papers = import_papers()
    persons = import_persons()
    orgs = import_orgs()
    platforms = import_platforms()

    counts = {
        "books": len(books),
        "papers": len(papers),
        "persons": len(persons),
        "orgs": len(orgs),
        "platforms": len(platforms),
    }
    for key, expected in EXPECTED.items():
        if counts[key] != expected:
            raise AssertionError(f"{key}: expected {expected}, got {counts[key]}")

    described = sum(1 for b in books if b["editorial"]["description"])
    if described != 610:
        raise AssertionError(f"expected 610 book descriptions, got {described}")

    authored = derive_authored_by(
        books, persons, lambda w: w["editorial"]["author"]
    ) + derive_authored_by(papers, persons, lambda w: w["editorial"]["authors"])

    edges = sorted(
        cat_edges + authored,
        key=lambda e: (e["edge_type"], e["from_id"], e["to_id"]),
    )

    _write_json(SEEDS_DIR / "books.json", books)
    _write_json(SEEDS_DIR / "papers.json", papers)
    _write_json(SEEDS_DIR / "persons.json", persons)
    _write_json(SEEDS_DIR / "orgs.json", orgs)
    _write_json(SEEDS_DIR / "platforms.json", platforms)
    _write_json(SEEDS_DIR / "edges.json", edges)

    n_authored = len(authored)
    lo, hi = AUTHORED_BY_BAND
    summary = {
        **counts,
        "descriptions": described,
        "categorized_as_edges": len(cat_edges),
        "authored_by_edges": n_authored,
        "conflict_flagged": [b["id"] for b in books if b["conflict_flag"]],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not (lo <= n_authored <= hi):
        print(
            f"WARNING: authored_by edges = {n_authored}, outside expected band "
            f"{lo}-{hi} (~168 +/-10%). Investigate before relying on the edge set."
        )
    else:
        print(f"authored_by edges = {n_authored} (within expected band {lo}-{hi}).")
    return summary


if __name__ == "__main__":
    run()
