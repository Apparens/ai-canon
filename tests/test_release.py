"""Sprint 3 — release builder, reproducibility, and adversarial review (CAN-15/16/17)."""

from __future__ import annotations

from pathlib import Path

import pytest

from canon import redteam
from canon import release as rel

_METRICS = Path(__file__).resolve().parents[1] / "data" / "resolved" / "metrics.json"

pytestmark = pytest.mark.skipif(
    not _METRICS.exists(), reason="no assembled metrics — run `make assemble` first"
)


def test_corpus_hash_is_stable_across_builds():
    a = rel._build_payload("test", "2026-06-29")["corpus_hash"]
    b = rel._build_payload("test", "2099-01-01")["corpus_hash"]  # date must not affect hash
    assert a == b


def test_build_then_verify_reproduces(tmp_path):
    # Build into a scratch root: the published release dirs are frozen (rule 11)
    # and must never be rewritten by the test suite.
    rel.build("_selftest", root=tmp_path)
    assert rel.verify("_selftest", root=tmp_path) is True


def test_committed_release_verifies_without_rebuild():
    # The published release must reproduce from the current inputs as committed.
    assert rel.verify() is True


def test_audit_bundle_is_self_contained_and_deterministic(tmp_path):
    import zipfile

    rel.build("_selftest", root=tmp_path)
    a = rel.bundle("_selftest", root=tmp_path).read_bytes()
    b = rel.bundle("_selftest", root=tmp_path).read_bytes()
    assert a == b  # byte-identical across builds (fixed timestamps, sorted entries)
    names = set(zipfile.ZipFile(tmp_path / "_selftest" / "audit-bundle.zip").namelist())
    # carries code, weights, pinned data, reproduce harness
    assert "src/canon/release.py" in names
    assert "scenarios.yaml" in names
    assert "data/resolved/metrics.json" in names
    assert "reproduce.sh" in names
    assert any(n.startswith("data/releases/_selftest/") for n in names)


def test_frozen_releases_are_byte_immutable():
    # [S15] Every registered release still hashes to its pinned tree sha256.
    frozen = rel._load_frozen()
    assert frozen, "FROZEN.json missing or empty: published releases must be pinned"
    assert rel.check_frozen() is True


def test_build_refuses_frozen_version():
    for version in rel._load_frozen():
        with pytest.raises(rel.ReleaseFrozenError):
            rel.build(version)
        with pytest.raises(rel.ReleaseFrozenError):
            rel.bundle(version)


def test_freeze_registry_is_append_only():
    already = next(iter(rel._load_frozen()))
    with pytest.raises(rel.ReleaseFrozenError):
        rel.freeze(already, "2099-01-01")


def test_redteam_gate_a_machinery_passes():
    # Review the committed release exactly as an outside reader would: no rebuild.
    summary = redteam.review()
    assert summary["gate_a_machinery"] == "PASS"
    assert summary["blocking_findings"] == 0
    # The single-metric divergence limitation must be DECLARED, not hidden.
    div = next(f for f in summary["findings"] if f["check"] == "scenario_divergence")
    assert div["status"] in ("declared-limitation", "observed")
