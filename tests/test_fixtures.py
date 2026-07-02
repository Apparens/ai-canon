"""The fixture corpus loads through the real schema models (no dead loaders)."""
from __future__ import annotations

from canon import fixtures
from canon.schema import Edition, Metric, Work


def test_fixture_corpus_validates_through_schema():
    works = fixtures.works()
    assert works and all(isinstance(w, Work) for w in works)
    editions = fixtures.editions()
    assert editions and all(isinstance(e, Edition) for e in editions)
    metrics = fixtures.metrics()
    assert metrics and all(isinstance(m, Metric) for m in metrics)
    # the multi-edition fixture the docstring promises (exercises the penalty path)
    assert sum(1 for e in editions if e.work_id == "book-aima") >= 2
