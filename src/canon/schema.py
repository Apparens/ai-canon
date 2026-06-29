"""Ontology v0.2 (FROZEN) implemented 1:1 in pydantic v2.

Canonical entities are scored. Context entities are curated, never ranked —
that is enforced structurally here, not by policy: ContextEntity has no score
field and forbids extra fields, so a `score` can never attach to a person,
organization, or platform (CLAUDE.md rule 7).

Do not "improve" this file. Changes to the ontology require a pilot finding,
not an opinion (master doc, Part II).
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# --- shared bases -----------------------------------------------------------


class _Frozenish(BaseModel):
    """Reject unknown fields so the frozen ontology cannot silently grow."""

    model_config = ConfigDict(extra="forbid")


class CanonicalEntity(_Frozenish):
    """Scored by evidence, ranked within its own domain only.

    The entity itself never stores a score: scores are computed per release
    from metrics + a scenario (see score.py) and are reproducible. Storing a
    score on the entity would let it drift away from its evidence.
    """

    canonical: Literal[True] = True


class ContextEntity(_Frozenish):
    """Curated and described, never ranked. NO score field exists — structural."""

    canonical: Literal[False] = False


# --- canonical: work + edition ---------------------------------------------

WorkType = Literal["book", "paper", "report", "standard"]


class Work(CanonicalEntity):
    """A book, paper, report, or standard.

    `category` is deliberately NOT a field — a work is multi-category, so
    category is expressed as a `categorized_as` Edge (master doc, Part II).
    """

    id: str
    canonical_title: str
    original_title: Optional[str] = None
    language: str
    year: Optional[int] = None
    work_type: WorkType
    level: Optional[str] = None
    # Conflict-of-interest flag, surfaced in the data itself (rule 12).
    conflict_flag: bool = False


class Edition(_Frozenish):
    canonical: Literal[False] = False
    work_id: str
    isbn_or_doi: Optional[str] = None
    language: str
    year: Optional[int] = None
    publisher: Optional[str] = None


# --- context: category, person, organization, platform ---------------------


class Category(_Frozenish):
    canonical: Literal[False] = False
    name: str
    axis: Literal["kind", "domain", "level", "orientation"]


class Person(ContextEntity):
    name: str
    category: Optional[str] = None
    known_for: Optional[str] = None
    bio: Optional[str] = None  # optional authored biography; shown where written
    source_url: Optional[str] = None  # checkable provenance for the entry (validated)
    anchor_affiliation: Optional[str] = None
    region: Optional[str] = None
    last_verified: Optional[date] = None


class Organization(ContextEntity):
    name: str
    category: Optional[str] = None
    what_it_is: Optional[str] = None
    region: Optional[str] = None
    last_verified: Optional[date] = None


class Platform(ContextEntity):
    name: str
    category: Optional[str] = None
    what_it_is: Optional[str] = None
    status: Optional[str] = None
    last_verified: Optional[date] = None


# --- evidence: metric -------------------------------------------------------


class Metric(_Frozenish):
    """A single evidence number. Rule 2: a number without provenance does not exist.

    `source`, `retrieved_at`, and `provenance_url` are mandatory and may not be
    blank — the validator rejects empty provenance rather than letting an
    unsourced number into the corpus.
    """

    work_id: str
    metric_name: str
    value: float
    source: str
    retrieved_at: date
    confidence: Literal["low", "medium", "high"]
    provenance_url: str
    license_note: str

    @field_validator("source", "provenance_url", "license_note")
    @classmethod
    def _non_blank(cls, v: str) -> str:
        if v is None or not str(v).strip():
            raise ValueError("metric provenance fields may not be blank (rule 2)")
        return v


# --- edges ------------------------------------------------------------------

# Allowed edge types only. The EXCLUDED set (influenced / promotes / critiques)
# is opinion dressed as data and is intentionally unrepresentable.
EdgeType = Literal[
    "categorized_as",
    "authored_by",
    "cited_in_syllabus",
    "has_metric",
    "cites",
    "works_at",
    "founded",
    "publishes",
    "maintains",
    "challenged_by",
    "decided_in",
]

VOLATILE_EDGES = {"works_at", "publishes", "maintains"}


class Edge(_Frozenish):
    from_id: str
    to_id: str
    edge_type: EdgeType
    source: str
    derivation_method: str
    last_verified: Optional[date] = None
    volatile: bool = False


# --- governance: append-only ------------------------------------------------


class Release(_Frozenish):
    governance: Literal[True] = True
    version: str
    date: date
    corpus_hash: str
    method_version: str
    changelog_ref: str


class Challenge(_Frozenish):
    governance: Literal[True] = True
    target_entity: str
    claimant_type: str
    rationale: str
    evidence_cited: str
    status: Literal["received", "upheld", "rejected"]
    resolution: Optional[str] = None
    release_applied: Optional[str] = None
    received_at: date
    resolved_at: Optional[date] = None


class Override(_Frozenish):
    governance: Literal[True] = True
    target_entity: str
    decision: str
    rationale: str
    decided_by: str
    date: date

    @field_validator("rationale")
    @classmethod
    def _rationale_required(cls, v: str) -> str:
        if v is None or not str(v).strip():
            raise ValueError("override rationale may not be empty (rule 5)")
        return v
