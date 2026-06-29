# The AI Canon: a method for auditable knowledge curation
### Corpus Cognitivum. Method note, version 1.0. Apparens public research initiative.

**Author:** Jeroen Janssen (Apparens, Deventer, Netherlands)
**Contact:** office@apparens.nl
**License:** CC BY 4.0
**Date:** 2026-06-29

---

## Abstract

The literature of artificial intelligence has outgrown any individual's ability to read it, and
the maps that exist are largely commercial: affiliate reading lists, vendor guides, and influencer
rankings that ask the reader to trust the curator. This note specifies a different approach. The
AI Canon is a public-good reference library whose rankings are produced by a published, deterministic
method over declared evidence, so that any reader can reproduce a result and challenge it. The claim
is narrow and testable: curation of knowledge can be made auditable, reproducible, and challengeable,
the way an account can be audited rather than taken on faith. The library is the product; the method
is the soul; any ranking is one view over the data. This note states the ontology, the scoring rules,
the handling of missing and multilingual evidence, the governance model, and the reproducibility
guarantee, together with an honest account of current coverage and deferred capabilities.

## 1. Premise

A rank in the AI Canon is not a verdict on intrinsic worth. It is a transparent output of declared
evidence, weights, and missing-data rules at a specific release date. The method exists to make that
output checkable end to end: the corpus, the weights, the per-work score breakdowns, and the code are
public, and a release rebuilds bit-for-bit from its audit package.

## 2. Ontology (v0.2, frozen)

The data model separates two kinds of entity, and the separation is structural rather than editorial.

- **Canonical entities** (work: book, paper, report, standard) are scored by evidence and ranked
  within their own domain only.
- **Context entities** (person, organization, platform) are described and never ranked. They carry
  no score field by construction, so ranking a human being is impossible in the model, not merely
  discouraged.

Category is expressed as an edge, not a field, because a work is multi-category. Governance records
(release, challenge, override) are first-class and append-only.

## 3. Scoring

Scoring is deterministic: identical inputs and weights produce identical ranks, reproducible from the
audit package with one command. Within a single domain, each metric is normalized (per-domain min-max
in the pilot), multiplied by its scenario weight, and summed. Domains never cross-rank: a standard is
never ranked against a monograph; a cross-domain ranking request raises an error rather than returning
a number. Weights live in a versioned `scenarios.yaml`, never in code. The pilot publishes three
scenarios (academic, broad influence, governance-practitioner) so the reader can see how a different
weighting produces a different canon.

## 4. Missing data

Missing evidence is recorded as missing and penalized by a published rule. No metric is estimated,
interpolated, or invented to fill a gap. Every per-work breakdown shows which metrics were present,
their values and provenance, and which were missing and the penalty applied.

## 5. Per-ecosystem normalization

The method commits, as a published rule, to scoring works within their own publishing and citation
ecosystem before any cross-language comparison, rather than against metrics from another ecosystem
that would erase them. This rule is written into the method. The mechanism that enforces it, and the
non-English corpus it requires, are still being built; until then the project makes no worldwide or
present-tense multilingual claim, and coverage gaps are declared. This is a deferred capability,
stated openly, not a silent stub.

## 6. Entity resolution

Records are never auto-merged below 0.95 confidence. Ambiguous pairs are routed to explicit human
override decisions, each with a written rationale. Distinct works with similar titles are kept apart;
a known fixture preserves the distinction between Charu C. Aggarwal's textbook and Michael Nielsen's
different online book of nearly the same name, and corrects a source misattribution.

## 7. Governance and independence

Anyone may challenge any entry, rank, metric, category, or method rule, including the maintainer's.
A challenge is contested against the cited evidence, not against opinion; each receives a public
identifier and a published resolution. Governance records are append-only: nothing is deleted, only
resolved. There is no advertising, no affiliate link, no sponsored placement, and no paid inclusion,
by rule and enforced in continuous integration. Works authored within Apparens carry a conflict flag
in the data and are scored by the same rules with no exemption and no boost.

## 8. Reproducibility

Each release ships a self-contained audit package: the pipeline code, the weights, the pinned data
snapshot, the per-work breakdowns, and a one-command reproduce script. The release carries a
`corpus_hash` over its exact inputs; rebuilding from the package must reproduce that hash bit for bit.
If a stranger cannot rebuild the ranking from the package, the release is defective and the maintainer
wants the challenge.

## 9. Coverage and limitations

The pilot scores the papers domain using openly licensed bibliographic metadata. Books are curated
and browsable but not yet scored. The corpus is strong in English; the multilingual layer is in
development and the Chinese-language spine is a known gap. The pilot's two harvested signals are
all-time citation count and readership persistence (the number of distinct years a work continues to
be cited, a longevity proxy). Additional signals (library holdings over time, edition count, syllabus
adoption) are declared and not yet harvested.

## 10. Legal and data use

The Canon uses bibliographic facts, public metadata, and lawfully accessible sources. It does not
republish copyrighted text, paywalled content, or proprietary datasets. Where a source's terms
restrict reuse, the Canon records derived signals only when lawful and otherwise omits the source and
declares the gap. Cover artwork is excluded by default.

## 11. How to cite

> Janssen, J. (2026). *The AI Canon: a method for auditable knowledge curation (Corpus Cognitivum).*
> Apparens public research initiative. Version 1.0. https://doi.org/PENDING

Replace `PENDING` with the DOI minted on deposit. Subsequent method versions cite the same concept DOI
with an incremented version, so the citation resolves to the version-of-record while pointing at the
living method.
