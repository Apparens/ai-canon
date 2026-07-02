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

import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .schema import Override

AUTO_MERGE_FLOOR = 0.95
OVERRIDES_DIR = Path(__file__).resolve().parents[2] / "data" / "overrides"


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


# --- the override channel (rule 5): ambiguous pairs are explicit human ---------
# --- decisions on disk, each with a mandatory rationale, append-only -----------


def _override_path(a_id: str, b_id: str) -> Path:
    lo, hi = sorted((a_id, b_id))  # order-insensitive key
    return OVERRIDES_DIR / f"{lo}__{hi}.json"


def record_override(a_id: str, b_id: str, decision: str, rationale: str,
                    decided_by: str, date: str) -> Path:
    """Write the human decision for an ambiguous pair. Validated through
    schema.Override (empty rationale raises, rule 5); existing records are
    never overwritten (governance records are append-only, rule 11)."""
    path = _override_path(a_id, b_id)
    if path.exists():
        raise FileExistsError(
            f"{path.name} already exists; override records are append-only. "
            "A changed decision is a NEW record for a new pair-state, not an edit."
        )
    record = Override(
        target_entity=f"{a_id}__{b_id}", decision=decision, rationale=rationale,
        decided_by=decided_by, date=date,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path


def load_override(a_id: str, b_id: str) -> dict | None:
    path = _override_path(a_id, b_id)
    if not path.exists():
        return None
    return json.loads(path.read_text("utf-8"))


def decide_final(a: Candidate, b: Candidate) -> dict:
    """decide(), then apply the recorded human decision for an ambiguous pair.

    No record => the pair stays BLOCKED: an ambiguous merge without a written
    rationale is exactly what rule 5 forbids ever happening silently."""
    result = decide(a, b)
    if result["action"] != "needs_override":
        return result
    record = load_override(a.work_id, b.work_id)
    if record is None:
        return {**result, "action": "blocked_pending_override"}
    return {**result, "action": f"override_{record['decision']}",
            "override": record}
