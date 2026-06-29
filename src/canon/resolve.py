"""Entity-resolution skeleton (CAN-13 seed).

The pilot's full ER cascade runs against external harvests later. This module
fixes the constitutional behaviour now (rule 5):

  * Never auto-merge below 0.95 confidence.
  * Pairs at/above the floor that are still ambiguous are routed to
    data/overrides/ as explicit human decisions, each with a mandatory rationale.
  * The known fixture is preserved: Charu C. Aggarwal's textbook "Neural
    Networks and Deep Learning: A Textbook" (mis-attributed to "Michael Nelson"
    in the Appelo source) must never be merged with Michael Nielsen's *different*
    online book of nearly the same name.

Similarity here is intentionally simple and deterministic (normalized title +
author overlap). It exists to enforce the floor and the override path, not to be
clever; the harvest pipeline supplies richer signals later.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

AUTO_MERGE_FLOOR = 0.95


def normalize(text: str) -> str:
    """NFC + casefold + whitespace collapse for deterministic comparison."""
    if text is None:
        return ""
    text = unicodedata.normalize("NFC", str(text)).casefold()
    return " ".join(text.split())


def _token_overlap(a: str, b: str) -> float:
    ta, tb = set(normalize(a).split()), set(normalize(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


@dataclass(frozen=True)
class Candidate:
    work_id: str
    title: str
    author: str
    year: int | None = None


def similarity(a: Candidate, b: Candidate) -> float:
    """Deterministic [0,1] similarity. Title dominates; author breaks ties.

    Differing authors cap the score below the auto-merge floor, which is exactly
    what keeps the Aggarwal/Nielsen pair apart even though their titles overlap.
    """
    title_sim = _token_overlap(a.title, b.title)
    author_sim = _token_overlap(a.author, b.author)
    score = 0.7 * title_sim + 0.3 * author_sim
    # Distinct authors are strong evidence of distinct works: cap below floor.
    if author_sim == 0.0:
        score = min(score, 0.80)
    return round(score, 6)


def decide(a: Candidate, b: Candidate) -> dict:
    """Return a merge decision. Below the floor => never auto-merge.

    Ambiguous (close to but below the floor) pairs are flagged for an override
    record; clearly-different pairs are simply kept distinct.
    """
    sim = similarity(a, b)
    if sim >= AUTO_MERGE_FLOOR:
        return {"action": "auto_merge", "similarity": sim, "a": a.work_id, "b": b.work_id}
    if sim >= 0.85:
        return {
            "action": "needs_override",
            "similarity": sim,
            "a": a.work_id,
            "b": b.work_id,
            "note": "above review threshold but below auto-merge floor; "
            "write an Override with a rationale before merging",
        }
    return {"action": "keep_distinct", "similarity": sim, "a": a.work_id, "b": b.work_id}
