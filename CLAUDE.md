# The AI Canon — project rules

## What this is
Public-good, reproducible, multilingual reference library of AI knowledge.
The ontology (Part II of the master doc) is FROZEN. The website (Part V) is in scope.
Build the method pipeline first (Stage A), then data population and site (Stages C–D).

## Hard rules (never violate, never "improve")
1. No ads, affiliate links, tracking, or sponsored-placement logic anywhere, ever.
2. Every metric row carries: source, retrieved_at, confidence, provenance_url, license_note.
3. Scoring is deterministic. Same input + same scenario = bit-identical output.
4. Domains never cross-rank: book/paper/report/standard each rank within their own domain;
   a cross-domain rank request raises an error.
5. Entity resolution never auto-merges below 0.95 confidence. Ambiguous cases go to
   data/overrides/ as explicit human decisions with a rationale. Empty rationale = invalid.
6. data/raw/ is write-once harvest output. Edits happen in overrides/, never in raw/.
7. Persons, organizations, platforms carry NO score field. Structural.
8. Never fabricate a metric. Missing data is recorded as missing and penalized by rule, not imputed.
9. Weights live in scenarios.yaml, not in code.
10. Any change to scoring logic or weights requires a changelog entry in the same commit.
11. Governance records (challenges, overrides, releases) are append-only.
12. Apparens-authored works carry conflict_flag: true (currently: "The AI Accountability Trap").
13. Lawful sources only: bibliographic facts and public metadata; never republish copyrighted text,
    paywalled content, or proprietary datasets. Restricted-source terms → derived signals only when
    lawful, otherwise omit and declare the gap.
14. No cover images by default. Publisher artwork only when clearly licensed for reuse.

## Workflow
- Plan mode before touching score.py or resolve.py.
- Run pytest before claiming any task complete.
- Releases: python -m canon.release, then git tag. Never hand-edit releases/.

## Style
- Python 3.12, pydantic v2, no ORM, no framework for the pipeline. Flat files + Git are the database.
- Small modules: a new contributor understands any file in 10 minutes.
