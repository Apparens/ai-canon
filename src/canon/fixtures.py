"""Load the hand-built fixture corpus (5 works) as validated schema objects.

Fixtures live as JSON under data/fixtures/ (data is data), and are validated
through schema.py on load so the demo and the tests exercise the real models.
The set covers: a plain book, a paper, one `standard`, a multi-edition book
(book-aima, two editions, deliberately missing syllabus_adoptions to exercise
the penalty), and a CN-translation work (book-cn, original_title in Chinese).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .schema import Edition, Metric, Work

_FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures"


def _load(name: str) -> list[dict]:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def works() -> list[Work]:
    return [Work(**w) for w in _load("works.json")]


def editions() -> list[Edition]:
    return [Edition(**e) for e in _load("editions.json")]


def metrics() -> list[Metric]:
    return [Metric(**m) for m in _load("metrics.json")]


def metrics_by_work() -> dict[str, list[Metric]]:
    out: dict[str, list[Metric]] = defaultdict(list)
    for m in metrics():
        out[m.work_id].append(m)
    return dict(out)


def works_of_type(work_type: str) -> list[Work]:
    return [w for w in works() if w.work_type == work_type]
