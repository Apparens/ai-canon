# Changelog

Append-only. Scoring-logic or weight changes must land with an entry here (rule 10).

## Chinese-language papers, and an importer that admits them (2026-06-30)

No scoring change: the new papers are candidates in the Chinese citation ecosystem, which
has no harvester yet, so they are browsable, not scored.

- The papers importer no longer hard-codes English. It reads a Lang column (default English) and a Source column, so a Chinese-language paper can enter as a work in its own ecosystem. The OpenAlex harvester now skips non-English papers by design: scoring a Chinese paper by its English-index citations would be exactly the cross-language comparison the method defers, so each is left as a declared gap for a future Chinese-ecosystem harvester.
- Added 12 foundational Chinese-language papers (the corpus's first), each verified against a source actually opened: Wu Wenjun's mechanization of geometry theorem proving (the Wu method, 1977), Li Deyi's cloud model (1995), Wang Fei-Yue's parallel systems (2004, the basis of ACP), the Zeng and Tan brain-inspired-intelligence survey (2016), two classic Chinese word-segmentation papers (N-shortest-path 2002, the decade review 2007), AI-law and AI-ethics work (Wu Handong 2017, the Zhang and Tan ethics survey 2021, Li Haiying on data-protection law 2020), and computer-vision and speech papers in Acta Automatica Sinica.
- Held back, not added: a 1990 monograph that is a book and not a paper (quotient-space theory), one segmentation paper whose proposed source resolved to a different work, and the two landmark national documents (the 2017 State Council AI plan, the 2021 national AI Ethics Norms), which are reports or standards rather than papers and would be a category error to file as papers.
- Counts: papers 214 to 226. Site copy counts updated accordingly.

## Chinese spine deepened (2026-06-30)

No scoring change: these are curated candidates, browsable not scored. The Chinese citation
ecosystem needs its own harvester, which stays deferred.

- Added 35 originally Chinese-language books (not translations), nearly doubling the Chinese spine from 28 to 63 works. Every one was verified against its live Douban page (title and author confirmed on the page); 2 candidates were dropped because the source did not confirm them, and a duplicate edition was merged out.
- Weighted toward the dimensions the spine was missing: 11 on AI ethics, governance, and law (Zhang Linghan on algorithm regulation; Xue Lan and Liang Zheng on AI governance frameworks; several AI-ethics texts), plus AI-and-society and philosophy (Zhao Tingyang, Jack Linchuan Qiu, the Berggruen Institute volume), computer vision, optimization theory, and an early Chinese neural-network classic (Jiao Licheng, 1990).
- Each carries its Douban source and a neutral AI-drafted description, flagged in the data like the rest of the corpus.
- Copy corrected: the method page and the China note now describe the spine as 63 curated books, browsable not scored, replacing the old "28 works" figure and the word "thin".

## pilot-v0.2: paper evidence harvest (2026-06-30)

A new frozen release. The method, weights, and ontology are unchanged (method_version
0.1-pilot); pilot-v0.1 stays on disk as the prior frozen record. What changed is the
evidence base: more papers now carry harvested metrics, so the ranking is computed over a
larger, stronger corpus. corpus_hash c379e0a8…, verified bit-identical on rebuild, GATE A pass.

- Harvested OpenAlex citation evidence for the papers added since launch (the notable-model papers), nearly doubling the scored set: 88 to 163 papers with at least one metric, 326 metrics total (was 174). Scenario divergence still observed.
- Every scored paper now has its own trust-surface page, not just the Top-50. A paper outside the Canon-50 links to its real evidence and real rank instead of showing "no evidence yet".
- Metric-matching hardened (entity resolution against OpenAlex): among duplicate records for one work, the canonical, most-cited record is chosen within a one-year window. This fixes cases where a zero-citation stub was picked over the real record, for example Mixtral of Experts now reads 122 citations, not 0.
- A zero from OpenAlex is treated as a declared gap, not a value: a fresh or unindexed record with no citations yet (Llama 3, Kimi K2, ERNIE 4.5) is shown as "no evidence yet", never as "0 citations", because a wrong number is worse than an honest gap.
- The recent model papers mostly rank below the long-cited classics, as the method intends: it rewards citations sustained across many years, which a 2025 paper has not had time to earn. They are scored and visible, not inflated.
- Release and site builds are now clean snapshots: a rebuild clears stale rankings, breakdowns, and work pages so changed evidence cannot leave orphaned files behind.

## Post-launch enrichment (2026-06-29)

No scoring-logic or weight changes. The pilot ranking is unchanged; the work below adds
provenance, descriptions, and corpus coverage, all as candidates pending evidence harvest.

### Provenance: every context entity is now checkable
- A source link on all 184 voices, an "about" link on all 133 organizations and 89 of 90 platforms (Papers with Code is defunct, left blank).
- A validation pass fixed real integrity problems: an entry that cited the Canon itself as its own source (removed), Wikipedia-as-primary and LinkedIn-only sources (replaced with official pages), and Google Scholar links that served readers a bot-block page. 33 sources upgraded to official pages.

### Voices: stale roles corrected, biographies added
- Web-verified the volatile current-role claims and corrected about 15 stale ones (lab moves such as Jumper to Anthropic, LeCun to AMI Labs, Wei to Meta); removed an internal "verify" note that had leaked into public text.
- Added a neutral, source-grounded biography to every voice. AI-drafted from each voice's cited source.

### Papers: model coverage, Chinese-first (162 to 214)
- Added 52 notable-model papers, each from its own primary arXiv or DOI, leading with Chinese labs (DeepSeek, Qwen, GLM, Kimi, Hunyuan, ERNIE, Pangu, Ling, LongCat, Seed and others). Cross-checked against Epoch AI's 2025 notable-models cohort; every arXiv id verified against the API to keep out a contaminated snapshot.
- Method page gains "What is not here, and why": the closed frontier (latest GPT, Claude, Gemini, Grok, Llama) ships system cards, not papers, so it cannot enter a paper canon; models enter only via a primary paper; stable arXiv/DOI sources are preferred; new entries are candidates.

### Models index
- New Models page: 68 models grouped by country and lab, each linking to its paper in the canon or shown as a declared "no paper, system card only" gap, plus an external link to the model. An index, described and linked, never ranked. Carries an as-of date and links Epoch AI for the live tracker.

### Library: every book now described (250 to 573)
- Wrote the 323 remaining book descriptions. Neutral and factual, AI-drafted from public sources and flagged as such in the data. No "Description pending" remains.

### Bibliographic reconciliation
- Reconciled all 573 books against OpenLibrary and 162 papers against Crossref and arXiv. Zero genuine errors (one book year corrected). A re-runnable tool with coverage records saved under data/validation.

### Transparency and security
- Site-wide AI-use disclosure (footer and a method note): ranks are computed not generated; voice biographies and many book descriptions are AI-drafted from public sources; the cover image is AI-generated.
- Social share icons (X, LinkedIn, email, GitHub) as inline SVG, CSP-safe.
- New gate guard [S14]: scans every tracked file for credential signatures, since the repo is public and the Zenodo archive is permanent.

## seed v0.3: Stage A skeleton + harvest layer (2026-06-29)

### Sprint 1 + CAN-07: method package & seed import
- Frozen ontology v0.2 in pydantic v2; context entities have no score field (structural).
- Deterministic, domain-isolated scorer; published missing-data penalty (factor 0.5);
  weights in `scenarios.yaml` (3 placeholder weightings).
- ER stub: no auto-merge < 0.95; Aggarwal != Nielsen.
- Imported seeds: 573 books / 162 papers / 183 persons / 132 orgs / 90 platforms;
  250 descriptions; 573 categorized_as + 172 authored_by edges; Trap conflict-flagged.

### Sprint 2: harvest layer (CAN-09 / CAN-10 / CAN-12)
- `data/raw/` write-once store with per-source sha256 manifest (rule 6).
- OpenAlex harvester: live fetch into the write-once cache; metrics derived from the
  cached snapshot (offline-deterministic); no match / offline => declared gap, never imputed.
- Manual CSV-drop path (WorldCat / Open Syllabus): each row carries provenance or fails.
- `canon.harvest.assemble`: derives + validates + dedupes metrics (highest confidence wins)
  into `data/resolved/metrics.json` with a `coverage.json` report.
- Scorer gains `--corpus` mode: ranks real works that have harvested evidence; works
  without evidence are an honestly-declared coverage gap, not a fabricated zero.

### Sprint 3: release builder, audit package, adversarial review (CAN-15/16/17)
- `canon.release`: frozen release under `data/releases/<version>/`: Top-50 per
  (domain, scenario), full per-work breakdowns, divergence summary, a `Release`
  governance record with a deterministic `corpus_hash` (date is metadata, not hashed),
  coverage.json, and REPRODUCE.md. `--verify` rebuilds and asserts bit-identical (rule 3).
- `canon.redteam`: adversarial-review harness: reproducibility, provenance completeness,
  domain isolation, no-imputation, conflict-flag surfacing, declared coverage, ranking
  sanity, divergence honesty → `reports/red_team_findings.md` + a GATE-A verdict.
- **Pilot release `pilot-v0.1`: GATE A PASS (substantive)**: 0 blocking findings; reproducible.
- Second independent signal derived from the SAME cached OpenAlex snapshot (no new network):
  `sustained_readership` = citations in 2023-2025 (recent momentum), distinct from all-time
  `citation_count`. Assembled 174 metrics (88 citation_count + 86 sustained_readership).
- With two signals the three scenarios now produce **different orderings**
  (`scenario_divergence: observed`). The method's central claim is demonstrated, not merely asserted.
- Adversarial loop ran the full two iterations: iteration 1 flagged a stale single-metric
  `ranking_sanity` check (false positive); fixed to assert composite-score monotonicity; iteration 2 clean.
- Still-declared gaps: `library_holdings` / `syllabus_adoptions` await WorldCat / Open Syllabus CSV
  drops; ~74 papers await the next OpenAlex daily-budget window.

### Stage C: public site (CAN-21..25)
- `canon.export_site`: static generator (no framework, no JS deps, no tracker code) emits
  `site/` from the release JSON + seeds: Canon-50 (3 scenario views), per-work breakdown
  pages (the trust surface: every metric + provenance + missing-data penalty), papers shelf,
  method, challenges, changelog, and a downloadable audit package under `site/audit/`.
- The approved homepage (`site/index.html`) is wired to the live pages; its Canon-50 teaser
  is GENERATED (top-3 injected by the builder, idempotent) so the manifesto never carries
  hand-typed ranking data that can drift.
- 59 pages, 621 internal links (0 broken), verified rendering in-browser. Deploy target:
  `apparens.nl/ai-canon/` (Cloudflare Pages, static).

### Design pass: align to apparens.nl + house style
- Generated chrome rewritten to mirror `apparens-design-system.css`: deep-blue fixed nav with
  the white Apparens logo + serif wordmark, white body, orange `#B8430A`, DM Serif + DM Sans.
- The homepage is now GENERATED too (page_home), in the same design, so the whole site is
  visually consistent and rebuilds from one place. Its Canon-50 teaser is the live top-3.
- House style: no em-dashes in any site copy (enforced by a test).

### Acceptance audit response (decisions 1 to 6)
- **Library shipped** (`library.html`): all 573 candidate books, filterable by category / language /
  provenance, descriptions where written and "Description pending" otherwise, conflict-of-interest flag
  shown inline, labelled candidacy not canonical. Books are curated and browsable but not yet scored.
- **Context shelves shipped**: `voices.html` (183), `organizations.html` (132), `platforms.html` (90),
  grouped by category, alphabetical within category, labelled "described, never ranked" (no score).
- Nav reordered so the Library leads: the reference library is the primary surface, the ranking is one view.
- Verbatim positioning line on the home page; verbatim humility clause on the Canon-50 and every per-work
  page; significance lines added to the papers shelf.
- Open data: the audit page now offers JSON and CSV for the full corpus (books + papers + context).
- **Declared deferrals** (stated on the method page, not silently stubbed): per-ecosystem normalization
  (rule 5) activates only when more than one ecosystem enters a scored domain, so the site makes no
  worldwide / present-tense multilingual claim and the Chinese spine (28 works) is a declared gap; a fuller
  longevity proxy (holdings over time, editions, availability); and book scoring. The pilot ranks papers
  only, behind honest framing, and that scored view passed GATE A.
- House style enforced at the render boundary: even verbatim seed text shows no em-dashes; a test fails
  the build on any em-dash in generated HTML.
- **Self-contained audit bundle (decision 3):** `canon.release` now emits `audit-bundle.zip`, a
  byte-deterministic archive carrying the pipeline code, weights, pinned data snapshot, release outputs,
  and a one-command `reproduce.sh`. Verified: extracted into a clean directory with no repo, it rebuilds
  the release and reports corpus_hash MATCH. This is what makes the package archival and time-invariant.

### Security hardening to the app's bar (v1.2, the [S##] guardrails)
Derived from the AI Control Index app's posture and adapted for a static site.
- Strict CSP in `site/_headers`: `default-src 'none'`, no `unsafe-inline` / `unsafe-eval`,
  plus X-Content-Type-Options, Referrer-Policy, X-Frame-Options DENY, COOP, CORP,
  Permissions-Policy, HSTS. [S5]
- All CSS and JS externalized to `site/assets/` so the strict CSP holds; no inline script or
  style remains in any page. [S6]
- Self-hosted the DM fonts (reused the owner's licensed woff2): zero third-party requests,
  no Google Fonts. [S7]
- Output safety: `esc()` escapes quotes too; `safe_url()` scheme-sanitizes data-derived hrefs
  (javascript:/data: collapse to `#`); adversarial XSS fixtures prove hostile titles,
  descriptions, and URLs cannot become markup or script. [S8]
- `scripts/static-gate.sh` runs all guardrails [S0]-[S13]; CI runs the gate; [S12] fails the
  build if ARCHITECTURE.md and the checks drift. ARCHITECTURE.md added with the [S##] system.
- [S13] Accessibility: a full axe-core pass across all 14 page types is clean (0 violations).
  Fixed body links to be underlined (distinguishable without color) and footer text contrast
  (a global `p` rule was rendering footer text dark-on-dark); promoted a heading to fix order.
  A static a11y lint (lang, single h1, img alt, heading order) keeps it from regressing in CI.
- 39 tests (8 security). The question behind this: if a million experts probe it, does it hold.

### Published
- Public repository: https://github.com/Apparens/ai-canon (MIT code + CC BY 4.0 corpus/method).
- Zenodo DOI minted via the GitHub release integration. Concept DOI (always latest):
  **10.5281/zenodo.21042034**. The method note, README badge, CITATION.cff, and the site Method
  page all cite it.

### Not yet
Book metric harvesting (title collisions: deferred), CN verification toward 60-90,
more harvested metrics (next OpenAlex daily window + WorldCat/Open Syllabus drops),
deploy the site to Cloudflare Pages.
