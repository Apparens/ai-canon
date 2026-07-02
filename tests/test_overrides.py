"""Rule 5's override channel and rule 8's fail-loud penalty, end to end."""
from __future__ import annotations

import pytest

from canon import resolve
from canon.resolve import Candidate
from canon.score import breakdown, load_scenarios
from canon.schema import Work

# Identical titles, 2/3 author-token overlap: 0.7*1.0 + 0.3*(2/3) = 0.9, squarely
# in the 0.85-0.95 review band (below the auto-merge floor, above keep_distinct).
A = Candidate("work-a", "Deep Learning Foundations and Practice", "Jane Q Doe", 2020)
B = Candidate("work-b", "Deep Learning Foundations and Practice", "Jane Doe", 2021)


def test_ambiguous_pair_needs_override():
    d = resolve.decide(A, B)
    assert d["action"] == "needs_override"
    assert 0.85 <= d["similarity"] < resolve.AUTO_MERGE_FLOOR


def test_ambiguous_pair_blocks_without_a_record(tmp_path, monkeypatch):
    monkeypatch.setattr(resolve, "OVERRIDES_DIR", tmp_path)
    assert resolve.decide_final(A, B)["action"] == "blocked_pending_override"


def test_empty_rationale_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(resolve, "OVERRIDES_DIR", tmp_path)
    with pytest.raises(ValueError):
        resolve.record_override("work-a", "work-b", "keep_distinct", "   ",
                                "jeroen", "2026-07-02")


def test_recorded_override_drives_the_decision_and_is_append_only(tmp_path, monkeypatch):
    monkeypatch.setattr(resolve, "OVERRIDES_DIR", tmp_path)
    resolve.record_override("work-a", "work-b", "keep_distinct",
                            "Different authors; verified distinct books.",
                            "jeroen", "2026-07-02")
    final = resolve.decide_final(A, B)
    assert final["action"] == "override_keep_distinct"
    assert final["override"]["rationale"].startswith("Different authors")
    with pytest.raises(FileExistsError):
        resolve.record_override("work-b", "work-a", "merge", "changed my mind",
                                "jeroen", "2026-07-03")  # order-insensitive, append-only


def test_missing_penalty_factor_fails_loudly():
    doc = load_scenarios()
    del doc["missing_data_penalty_factor"]
    w = Work(id="w1", canonical_title="T", language="en", work_type="paper",
             conflict_flag=False)
    with pytest.raises(KeyError):
        breakdown(w, [], "academic", doc, {})


def test_present_components_carry_license_note():
    from canon import fixtures
    from canon.score import rank_within_domain

    rows = rank_within_domain(fixtures.works_of_type("book"),
                              fixtures.metrics_by_work(), "academic")
    present = [c for r in rows for c in r["components"] if c["status"] == "present"]
    assert present and all(c.get("license_note") for c in present)
