"""Constitutional tests — these encode the rules the pipeline may not break."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from canon import fixtures, ingest
from canon.resolve import AUTO_MERGE_FLOOR, Candidate, decide, similarity
from canon.schema import Metric, Person
from canon.score import CrossDomainError, load_scenarios, rank_within_domain, to_json

REPO = Path(__file__).resolve().parents[1]
SEEDS = REPO / "data" / "seeds"


# --- rule 3: determinism ----------------------------------------------------


def test_scoring_is_bit_identical_across_runs():
    works = fixtures.works_of_type("book")
    mbw = fixtures.metrics_by_work()
    a = to_json(rank_within_domain(works, mbw, "academic"))
    b = to_json(rank_within_domain(works, mbw, "academic"))
    assert a == b


# --- rule 4: domains never cross-rank --------------------------------------


def test_cross_domain_ranking_raises():
    mixed = [
        next(w for w in fixtures.works() if w.work_type == "book"),
        next(w for w in fixtures.works() if w.work_type == "standard"),
    ]
    with pytest.raises(CrossDomainError):
        rank_within_domain(mixed, fixtures.metrics_by_work(), "academic")


# --- rule 8: missing data recorded + penalized, never imputed ---------------


def test_missing_metric_is_penalized_not_imputed():
    rows = rank_within_domain(
        fixtures.works_of_type("book"), fixtures.metrics_by_work(), "academic"
    )
    aima = next(r for r in rows if r["work_id"] == "book-aima")
    missing = [c for c in aima["components"] if c.get("status") == "missing"]
    assert any(c["metric"] == "syllabus_adoptions" for c in missing)
    penalty = next(c for c in missing if c["metric"] == "syllabus_adoptions")
    scen = load_scenarios()
    expected = round(
        scen["scenarios"]["academic"]["weights"]["syllabus_adoptions"]
        * scen["missing_data_penalty_factor"],
        6,
    )
    assert penalty["missing_data_penalty"] == expected
    # The missing metric must NOT appear as a present/imputed value.
    assert all(
        not (c["metric"] == "syllabus_adoptions" and c.get("status") == "present")
        for c in aima["components"]
    )


# --- rule 7: context entities carry NO score field (structural) -------------


def test_person_has_no_score_field():
    assert "score" not in Person.model_fields
    with pytest.raises(ValidationError):
        Person(name="Test Voice", score=1.0)


# --- rule 2: a number without provenance does not exist ---------------------


def test_metric_without_provenance_is_rejected():
    with pytest.raises(ValidationError):
        Metric(
            work_id="x",
            metric_name="citation_count",
            value=1.0,
            source="OpenAlex",
            retrieved_at="2026-06-14",
            confidence="high",
            provenance_url="",  # blank provenance is invalid
            license_note="CC0",
        )


# --- rule 5: ER never auto-merges below 0.95; Aggarwal != Nielsen -----------


def test_aggarwal_and_nielsen_are_kept_distinct():
    aggarwal = Candidate(
        "book-agg", "Neural Networks and Deep Learning: A Textbook", "Charu C. Aggarwal", 2018
    )
    nielsen = Candidate(
        "book-nie", "Neural Networks and Deep Learning", "Michael Nielsen", 2015
    )
    assert similarity(aggarwal, nielsen) < AUTO_MERGE_FLOOR
    assert decide(aggarwal, nielsen)["action"] != "auto_merge"


def test_identical_work_auto_merges_above_floor():
    a = Candidate("a", "Deep Learning", "Ian Goodfellow Yoshua Bengio", 2016)
    b = Candidate("b", "Deep Learning", "Ian Goodfellow Yoshua Bengio", 2016)
    assert decide(a, b)["action"] == "auto_merge"


# --- CAN-07: committed seeds are schema-valid and have the right counts ------

EXPECTED_FILES = {
    "books.json": 573,
    "papers.json": 214,
    "persons.json": 184,
    "orgs.json": 133,
    "platforms.json": 90,
}


@pytest.mark.skipif(
    not (SEEDS / "books.json").exists(), reason="seeds not generated yet"
)
@pytest.mark.parametrize("name,count", EXPECTED_FILES.items())
def test_seed_counts(name, count):
    import json

    data = json.loads((SEEDS / name).read_text(encoding="utf-8"))
    assert len(data) == count


@pytest.mark.skipif(
    not ingest.BOOKS_XLSX.exists(), reason="source workbooks not present (CI)"
)
def test_ingest_is_deterministic():
    first = ingest.run()
    books_a = (SEEDS / "books.json").read_bytes()
    ingest.run()
    books_b = (SEEDS / "books.json").read_bytes()
    assert books_a == books_b
    assert first["books"] == 573 and first["descriptions"] == 250
