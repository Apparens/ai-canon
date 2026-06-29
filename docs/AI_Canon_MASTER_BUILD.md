# THE AI CANON — MASTER BUILD DOCUMENT
### Single source of truth for Claude Code. 29 June 2026. Apparens public research initiative.

This one document contains everything needed to build The AI Canon end to end: the strategy that
constrains it, the frozen ontology it implements, the curated data that populates it, the website and
infrastructure to host it, and the staged build plan. Where this document and any older file disagree,
**this document wins.**

**North star:** *Nothing is for sale. Nothing is hidden. Nothing is final.*

**What the owner wants built (plain statement of intent):**
> The pages, the database, and the infrastructure, live on my website, populated with all the content.

So this is no longer only a scoring pilot. It is a full public reference website backed by a reproducible
method pipeline. Both halves are specified below. Build order still puts the method pipeline first
(it is the soul and the hardest part), but the website and data population are now in scope, not deferred.

---

# PART I — WHAT THIS IS (constraints you may not break)

The AI Canon is a **public-good reference library** for AI knowledge. Free, method-backed, sells nothing.
It is a **reference work with rankings as one view**, not a ranking. The library is the product; the
method is the soul; any Top-N list is a view over the data.

**Positioning line (verbatim, used on the site):**
> The AI Canon is a free, method-backed reference library for AI knowledge. It ranks texts, not people. It invites correction. It sells nothing.

**The keystone decision — canonical vs context:**
- **Canonical entities** (book, paper, report, standard) are **scored** by evidence, ranked **within their own domain only**.
- **Context entities** (person, organization, platform) are **described, never ranked**. They carry no score field. This is structural, not a policy: ranking people is impossible by construction.

**Community input is challenge, never vote.** Readers may nominate missing works or argue promotion/
demotion, but only through the challenge protocol: every suggestion is an evidence-bound, append-only
**challenge** with a public ID and a published resolution. There is no form that writes to the corpus and
no score that moves by popularity. This keeps an open door without turning a curated canon into a
popularity contest.

**Eight constitutional method rules** (published with every release; never violated):
1. Deterministic scoring — identical inputs + weights → bit-identical ranks; reproducible from the audit package with one command.
2. Provenance on every number — source, retrieved_at, confidence, licence note. A number without provenance does not exist.
3. No silent imputation — missing evidence recorded as missing and penalized by published rule, never estimated.
4. Domains never cross-rank — a standard is never ranked against a monograph.
5. Per-ecosystem normalization first — Chinese works score on Chinese-ecosystem evidence (Douban, union catalogues, MOE 规划教材 designations) before any cross-lingual comparison; coverage gaps declared.
6. People are context, never contestants.
7. Manual decisions are records — every override carries a written rationale and is published; Apparens-authored works carry a conflict flag in the data.
8. Humility on rank — *a rank is not a verdict on intrinsic worth. It is a transparent output of declared evidence, weights, and missing-data rules at a specific release date.*

**Legal & data use (constitutional):** bibliographic facts, public metadata, and lawfully accessible
sources only. Never republish copyrighted text, paywalled content, or proprietary datasets. Where a
source's terms restrict reuse, record derived signals only when lawful, otherwise omit the source and
declare the gap. **No cover images by default** — text, metadata, and provenance only, unless a cover is
clearly licensed for reuse.

**Funding & independence (absolute):** no advertising, no affiliate links, no sponsored placement, no paid
inclusion, ever. CI-enforced: no ad/affiliate/tracker code paths may exist in the repo.

**Coverage honesty:** the corpus is strong in English. The multilingual layer is in development and the
**Chinese-language spine is a known gap** (28 works; target 60–90, quality-bounded). The site does **not**
claim "worldwide" until that gap closes. Chinese-literate readers are invited to nominate and contest via
the challenge protocol.

**Maintenance promise (verbatim):**
> Every update is logged. Every correction is traceable. Every ranking can be challenged. The library is maintained as capacity allows — without deadlines we would resent, and without commercial influence of any kind.

**Stop conditions:** (1) pilot Top 50 fails internal adversarial review after two iterations → stop and
rethink method; (2) CN coverage below floor → descope the multilingual claim; (3) maintenance honestly
abandoned → archive with a dated final release rather than let it rot.

**Names & contact:** product name "The AI Canon". Latin masthead *Corpus Cognitivum* (neuter — never
"Cognitivus") allowed on the method paper, **not** on the public page. Challenge mailbox for launch:
**office@apparens.nl** (a `canon@` alias may replace it later without changing the protocol).

---

# PART II — THE FROZEN ONTOLOGY (implement exactly)

Ontology **v0.2 is FROZEN**. Schemas implement this 1:1. Do not "improve" it; changes require a pilot
finding, not an opinion.

```yaml
version: 0.2
status: frozen_for_pilot

# CANONICAL entities are scored. CONTEXT entities are curated, never ranked.

entity_types:
  work:
    canonical: true
    subtypes: [book, paper, report, standard]   # 'standard' = ISO 42001, NIST AI RMF, OECD Principles:
                                                 #   canonical but DIFFERENT metric profile; scored within type.
                                                 # 'report' acknowledged underspecified; split only if pilot shows it matters.
    key_fields: [canonical_title, original_title, language, year, work_type, level]
    # category is NOT a field — it is an edge (categorized_as), because works are multi-category.
  edition:
    canonical: false
    key_fields: [isbn_or_doi, language, year, publisher]
  category:
    canonical: false
    key_fields: [name, axis]          # axes: kind / domain / level / orientation
  person:
    canonical: false                  # NEVER ranked — no score field exists
    key_fields: [name, category, known_for, anchor_affiliation, region]
  organization:
    canonical: false
    key_fields: [name, category, what_it_is, region]
  platform:
    canonical: false
    key_fields: [name, category, what_it_is, status]
  metric:
    canonical: false
    key_fields: [source, metric_name, value, retrieved_at, confidence, provenance_url, license_note]
    # Future (post-pilot, noted not built): source_reliability, coverage, freshness.

  # GOVERNANCE ENTITIES — append-only, public:
  release:
    governance: true
    key_fields: [version, date, corpus_hash, method_version, changelog_ref]
  challenge:
    governance: true
    key_fields: [target_entity, claimant_type, rationale, evidence_cited, status, resolution, release_applied, received_at, resolved_at]
  override:
    governance: true
    key_fields: [target_entity, decision, rationale, decided_by, date]

relationships:
  categorized_as:     {from: work, to: category, derivable_now: true}   # multi-tagging
  authored_by:        {from: work, to: person, derivable_now: true}     # ~168 edges derivable today
  cited_in_syllabus:  {from: work, to: platform, derivable_now: false, source: open_syllabus_tierB}
  has_metric:         {from: work, to: metric, derivable_now: false, source: harvesters}
  cites:              {from: work, to: work, derivable_now: false, source: bibliography_pipeline}
  works_at:           {from: person, to: organization, volatile: true}
  founded:            {from: person, to: organization, volatile: false}
  publishes:          {from: organization, to: platform, volatile: true}
  maintains:          {from: organization, to: platform, volatile: true}
  challenged_by:      {from: work, to: challenge, derivable_now: true}
  decided_in:         {from: challenge, to: release, derivable_now: true}
  # EXCLUDED: influenced, promotes, critiques — opinion dressed as data; not edges.

edge_rules:
  - every edge carries: source, derivation_method, last_verified
  - volatile edges expire: re-verify each release or mark stale
  - no LLM-inferred edge without a human-auditable derivation rule
  - governance entities are append-only: never deleted, only resolved
```

---

# PART III — THE DATA (what populates the library)

All seed data is in the project space as spreadsheets. Convert to JSON, validate against the schema,
write to `data/seeds/`. **Authoritative counts (verified 29 June 2026):**

| File | Sheet | Rows | Notes |
|---|---|---|---|
| `AI_Canon_SeedCorpus_v03.xlsx` | SeedCorpus | **573 books** | All categorized. 250 have curated descriptions; 323 await authoring (mostly the 299 hunt + 24 obscure Monett rows). Cols: Nr, Title, Author, Year, Lang, Category, DescConfidence, Source, Description |
| | ReadMe | — | semantics & provenance |
| `AI_Canon_Papers_Seed.xlsx` | (first) | **162 papers** | 1943–2025, venue + significance + confidence |
| `AI_Canon_Voices_Orgs_Platforms.xlsx` | Voices | **183** | context — never ranked |
| | Organizations | **132** | context — never ranked |
| | Platforms | **90** | context — never ranked, has Status column |

**Book corpus provenance breakdown:** Appelo core 201 (all described), Canon hunt 299, Monett Critical-AI
14th ed 73 (provenance-tagged; 48 of Monett's titles were already held and are not double-counted).

**Languages in the book seed:** EN 531, ZH 28, DE 5, ES 3, NL 2, plus FR/JA/CS singletons. The ZH 28 is
the known gap; do not let any "worldwide" copy ship until it reaches 60–90 verified.

**DescConfidence semantics:** this column is confidence in the *description/metadata*, NOT canonical
evidence. Canonical evidence (citations, holdings, syllabus use) is computed by the pipeline, never
hand-asserted. Low-confidence rows with empty descriptions are flagged for the Stage D authoring pass.

**Known ER fixture to preserve:** the Appelo source attributed "Neural Networks and Deep Learning: A
Textbook" to "Michael Nelson"; the work is **Charu C. Aggarwal's** (corrected in the description). Also,
Michael Nielsen's online "Neural Networks and Deep Learning" is a **different** work — ER tests must keep
them apart.

**Other project files:** `ai-canon-index.html` is the approved public homepage (Part V). `AI_Books_Library.xlsx`
is the original 201 with descriptions — keep as description-provenance reference, do not import.
`AI_Canon_SeedCorpus_v02.xlsx` and `AI_Canon_500_Candidates.xlsx` are **superseded** by v0.3 — do not import.

---

# PART IV — REPO, CONSTITUTION, PIPELINE

## CLAUDE.md (place verbatim in repo root)

```
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
```

## Repo layout

```
ai-canon/
├─ CLAUDE.md
├─ data/
│  ├─ seeds/        # books.json, papers.json, persons.json, orgs.json, platforms.json
│  ├─ raw/          # per-source harvests (openalex/ worldcat/ opensyllabus/ douban/)
│  ├─ resolved/     # works.json post-ER; cn_en_mapping.json
│  ├─ overrides/    # one JSON per manual decision, with rationale
│  └─ releases/     # frozen audit packages per tag
├─ src/canon/       # schema.py, harvest/, resolve.py, score.py, release.py, export_site.py
├─ scenarios.yaml
├─ site/            # the public website (Part V)
├─ tests/
└─ reports/         # top50_comparison.md, red_team_findings.md
```

## Data conversion notes
- Convert xlsx → JSON with openpyxl/pandas; validate every row against schema.py before writing seeds.
- Books: `work_type=book`; `Lang`→`language`; `Category`→`categorized_as` edge (single tag now, model supports many); keep `DescConfidence`, `Source`, `Description` verbatim.
- Papers: `work_type=paper`; venue + significance preserved.
- Context entities: import as-is; stamp every row `last_verified: 2026-06-14`; affiliations are volatile.
- Derive `authored_by` edges by full-name containment after Unicode normalization; expect ≈168 (±10%); investigate larger drift.

---

# PART V — THE WEBSITE & INFRASTRUCTURE (now in scope)

The owner wants pages, database, and infrastructure live on the Apparens website, populated with all
content. Design constraints, then build.

## Architecture decision: static-first, data-driven

The whole site is **statically generated from the canonical JSON** and served from **Cloudflare Pages**.
There is no application server and no live database for the public site — the "database" is the versioned
JSON/CSV in the repo, and pages are generated from it at build time. Rationale: it matches NFR-13/14/17
(static, longevity, consumable without the site), it has near-zero maintenance and cost (correct for a
public good), and it cannot leak or be injected because there is no live backend. The **only** dynamic
write path is the challenge mailbox (email), exactly as the method requires.

- **Host:** Cloudflare Pages (Apparens already uses Cloudflare; deploy as `apparens.nl/ai-canon/`).
- **Build:** `python -m canon.export_site` reads `data/releases/<current>` + seeds and emits `site/` as
  plain HTML + a small JSON payload per shelf for client-side filtering. No framework required; if a
  build tool helps, a minimal one is fine, but the output must be static files.
- **Styling:** reuse the Apparens design system already in `ai-canon-index.html` (DM Serif Display, DM Sans,
  DM Mono; navy #0E2A4A, cream #F4EEE2, orange #E87722). Keep it self-contained, no external JS deps.
- **Data for the browser:** ship each shelf as a compressed JSON file lazy-loaded on its page; filtering and
  sorting happen client-side with vanilla JS. No localStorage/sessionStorage. No cookies beyond none.

## Page map (what to generate)

1. **Home** — `ai-canon-index.html` already exists and is approved (nine clauses, Canon-50 pending-stamp).
   Wire its nav to the pages below. At launch, replace the empty Canon-50 stamp table with the real
   ranked 50 once Stage A produces it.
2. **The Canon 50** — `/ai-canon/canon-50/` — three scenario views (academic / broad influence /
   governance-practitioner), each rank linking to its **score breakdown** page (every metric, source,
   retrieval date, weight). This is the method made visible.
3. **Library (books)** — `/ai-canon/library/` — all 573 candidate works, filter by category / level /
   language / provenance, descriptions shown where present, "description pending" where not. Honest about
   seed-vs-scored status.
4. **Papers** — `/ai-canon/papers/` — the 162, with significance lines; OpenAlex citation column once
   harvested.
5. **Voices / Organizations / Platforms** — `/ai-canon/voices/` etc. — the context shelves, **clearly
   marked "described, never ranked,"** alphabetical within category, affiliations shown with a
   last-verified date.
6. **Method** — `/ai-canon/method/` — the eight rules, the ontology summary, the weighting scenarios, the
   inclusion floor, in full. Links to the Zenodo method note (DOI).
7. **Challenges** — `/ai-canon/challenges/` — the public challenge log: every challenge ID, its target,
   status, and resolution. Append-only. This page IS the differentiator; build it even when near-empty.
8. **Changelog** — `/ai-canon/changelog/` — append-only release history.
9. **Audit / Data** — `/ai-canon/data/` — download the current audit package and the corpus as JSON/CSV
   (openly licensed), plus the one-command reproduction instructions.

## Per-work score-breakdown page (the trust surface)
For each scored work, generate a static page showing: final score per scenario, every metric with its
value/source/retrieved_at/confidence/provenance_url, the weight applied, the missing-data penalties, and a
"challenge this rank" link to office@apparens.nl pre-filled with the work ID. If a stranger cannot see
exactly why a work scored what it scored, the page is incomplete.

## Infrastructure NFRs (site)
- LCP < 2.5s on mid-range mobile; core reading works with **no JS**; filtering enhances, never gates.
- WCAG 2.1 AA; keyboard-navigable tables.
- Full Unicode; CJK titles render in every view; store original script + romanization.
- The canon is consumable as plain JSON/CSV without the site (longevity).
- Cookieless, trackerless; the mailbox is the only inbound data path; CI greps for and fails on any
  ad/affiliate/tracker code.

---

# PART VI — BUILD PLAN (staged, with gates)

Feature IDs continue the CAN-xx series. Build the pipeline first; the site consumes its output.

## Stage A — Method Package (the soul; do first)
**Sprint 1 — contract & skeleton:** CAN-01 repo + CLAUDE.md + CI; CAN-02 pydantic schemas implementing the
frozen ontology (incl. governance entities, no-score-on-context); CAN-03 scenarios.yaml (3 weightings);
CAN-04 deterministic scorer with **domain isolation** (cross-domain rank → error); CAN-05 missing-data
penalty; CAN-06 fixtures (5 works incl. multi-edition, CN translation, one `standard`).
**Sprint 2 — seeds & harvest:** CAN-07 import all seeds from the v0.3 workbook + papers + context →
schema-valid JSON (573 + 162 + 405 load clean; 250 descriptions intact); CAN-08 CN verification pass toward
60–90 (flag unverified); CAN-09 OpenAlex harvester; CAN-10 WorldCat + Open Syllabus (manual CSV drop OK for
pilot); CAN-11 Douban harvester (rate-disciplined, cache, CSV fallback); CAN-12 raw/ immutability checks.
Goodreads: omitted-and-declared.
**Sprint 3 — resolution, scoring, red team:** CAN-13 ER cascade (no auto-merge < 0.95; Aggarwal/Nielsen
fixture passes); CAN-14 cn_en_mapping hand-reviewed; CAN-15 release builder (Top 50 per scenario,
breakdowns, divergence analysis); CAN-16 audit package (one-command reproduce); CAN-17 internal adversarial
review (two-iteration limit).
**GATE A (hard):** pilot Top 50 survives adversarial review within two iterations.

## Stage B — Soft validation
CAN-18 share pilot + audit file with ~10 trusted readers (2+ CN-ecosystem); CAN-19 listen for: would they
use it, do they bother to attack it, canon-or-atlas (verdict-first vs map-first); CAN-20 one-page findings,
adjust weights/framing if warranted. **GATE B (soft):** no go/no-go; findings inform launch framing only.

## Stage C — Publish the site
CAN-21 deploy `ai-canon-index.html` + wire nav; confirm office@apparens.nl receives; CAN-22 generate the
real Canon 50 (3 views) replacing the pending stamp, each rank → breakdown page; CAN-23 publish audit
package download (Part V §9); CAN-24 method note → Zenodo, DOI live **at** publication; CAN-25 changelog +
challenge log pages armed; CAN-26 quiet distribution (the ~10 readers + the curators whose lists seeded the
corpus, incl. Monett + Appelo, + NL network). No superlatives. **GATE C:** live, reproducible, challengeable.

## Stage D — Full library build-out (as capacity allows)
CAN-27 Library browse page (all 573, filters) — the community-value page; CAN-28 author the ~323 missing
descriptions + "known weakness/controversy" field — the unrebuildable editorial layer; CAN-29 context-shelf
pages (curated slices first), affiliations re-verified; CAN-30 Papers page + OpenAlex column; CAN-31 refresh
automation (harvest → diff → anomaly flags >20% → release-candidate PR → one human approval gate); CAN-32
Books full ranked release (post-classifier, inclusion floor published); CAN-33 `cites` pilot (15–20 books),
separately gated — drop the layer if no expert would defend its top papers.

**NOT building, ever (public-good pin):** user accounts, community voting, credentialed tiers, paid
analytics, APIs/subscriptions, dashboards, AI chat over the Canon. Revisit only on demonstrated community
pull, and even then only through challenge-protocol-compatible designs.

## First prompt to paste into Claude Code
> Read CLAUDE.md and Parts I–IV of the master build document. We are in Stage A, Sprint 1. Plan first, then
> build: pydantic schemas implementing the frozen ontology exactly (governance entities included; context
> entities have no score field), scenarios.yaml with three placeholder weightings, fixtures for 5 works
> (multi-edition, CN translation, one standard), and a deterministic end-to-end scoring pipeline on fixtures
> with per-work breakdowns and domain isolation. Tests: determinism, missing-data penalty, duplicate
> detection, cross-domain ranking raises. Stop after the plan and show it to me.

---

# PART VII — DEFINITION OF DONE

**Pilot (Gate A/C):** a stranger holding only the audit package can rebuild the Top 50 with one command,
read on a per-work page exactly why every work scored what it scored, and file a challenge against any
number they disagree with.

**Website (Stage C/D):** every shelf is browsable and honest about its status; every scored rank links to
its evidence; the challenge log and changelog are live and append-only; the whole corpus downloads as open
JSON/CSV; nothing on the site is for sale and no tracker exists; and the site rebuilds deterministically
from the repo with one command.

When both are true, The AI Canon exists. Everything else is a view.

---

## Open items (owner, outside the build)
1. **office@apparens.nl** — confirm it is monitored before Stage C. (Address already set in page + docs.)
2. **CN collaborator** — public call to Chinese-literate readers to nominate + contest via challenge
   protocol, credited; plus a sought named CN-ecosystem reviewer. Gates the "worldwide" claim only.

## Document supersessions (for a clean project space)
- PRIMARY book seed: `AI_Canon_SeedCorpus_v03.xlsx`. Superseded: v02, `AI_Canon_500_Candidates.xlsx`.
- This master doc supersedes: `AI_Canon_Strategy_v0.4_FINAL.md`, `AI_Canon_Sprintplan_v2.md`,
  `HANDOFF_claude_code.md`, `ontology_v0.2_frozen.md` (all now folded in here). Keep them only as history.
- Live homepage artifact: `ai-canon-index.html` (synced to v0.3 counts).
