# The AI Canon, architecture

*Single source of truth for how the Canon is built, served, and kept safe. Mirrors the
discipline of the AI Control Index app: every hardening guardrail is numbered `[S##]`,
every `[S##]` has a check in `scripts/static-gate.sh`, and the gate fails on drift between
this document and the checks.*

North star: **Nothing is for sale. Nothing is hidden. Nothing is final.**

---

## Version history

> **v1.2 (2026-06-29)** Security hardening to the app's bar. Externalized all CSS/JS so the
> CSP forbids inline script and style (`[S5]`, `[S6]`); self-hosted the DM fonts so there is
> zero third-party request (`[S7]`); added `_headers` with a strict `default-src 'none'` CSP
> and the full security-header set; added URL-scheme sanitization and adversarial XSS tests
> (`[S8]`); introduced the `[S##]` guardrail system, `scripts/static-gate.sh`, and this
> document. Gate: 13 guardrails, 38 tests.

> **v1.1 (2026-06-29)** Acceptance-audit response: shipped the Library and the three context
> shelves (the reference library is the primary surface), verbatim positioning and humility
> clauses, declared deferrals, and the self-contained reproducible audit bundle.

> **v1.0 (2026-06-29)** Stages A through C: frozen ontology, deterministic scorer, OpenAlex
> harvest, GATE-A release, and the static public site generated from the release JSON.

---

## What it is

A free, public, method-backed reference library of the texts that define AI. The library is
the product; the method is the soul; any ranking is one view over the data. It ranks texts,
never people. See `docs/AI_Canon_MASTER_BUILD.md` for the full strategy and frozen ontology.

## Principles

1. Evidence before assertion. Every number carries its provenance or it does not exist.
2. The method is public and reproducible. A stranger can rebuild any release.
3. People are context, never contestants (structural: context entities have no score field).
4. Honesty about coverage. Gaps are declared, never zero-filled or invented.
5. No commercial influence, ever. No ads, affiliates, sponsorship, tracking, or cookies.
6. Static by construction. No backend, no database, nothing to leak or inject.
7. House style: no em-dashes in copy.

---

## Technical architecture

- **Language / stack:** Python 3.12, pydantic v2. Flat files + Git are the database. No ORM,
  no framework. The public site is plain static HTML/CSS/JS.
- **Pipeline modules** (`src/canon/`): `schema.py` (frozen ontology v0.2), `score.py`
  (deterministic, domain-isolated scorer), `resolve.py` (entity-resolution guards),
  `ingest.py` (seed import), `harvest/` (OpenAlex harvester, OpenLibrary harvester
  [future-stage, unwired by design: books carry no metrics yet], CSV-drop, assemble),
  `release.py` (release builder, freeze registry, self-contained audit bundle),
  `redteam.py` (adversarial review, one function per check), `export_site.py` (site build
  orchestrator) + `sitegen/` (theme, shell, page renderers, JS assets), `raw.py` (write-once
  harvest store with sha256-verified reads), `textnorm.py` (the one text-normalization
  helper), `fixtures.py` (demo fixtures).
- **Build:** `make ingest | harvest | assemble | release | site`. The site is generated
  deterministically from `data/releases/<version>/` + `data/seeds/`. CSS and JS are emitted as
  external files (`site/assets/canon.css`, `site/assets/canon.js`); fonts are self-hosted
  (`site/assets/fonts/`, `site/assets/fonts.css`).
- **Serving:** Cloudflare Pages, static, deploy root = `site/` only (no source, no data
  pipeline, no secrets ship). `site/_headers` carries the CSP and security headers.
- **The only inbound data path** is the challenge mailbox (`office@apparens.nl`). There is no
  form, endpoint, or write path on the public site.

## Page map

`index.html` (manifesto + live Canon-50 teaser), `search.html` (client-side, no backend),
`library.html` (the full book shelf, filterable), `canon-50.html` (3 scenario views),
`work/<id>.html` (per-work trust surface), `papers.html` (with verbatim abstracts),
`frontier.html` (the research-frontier map), `models.html` (index, never a leaderboard),
`voices.html` / `organizations.html` / `platforms.html` (context shelves, described never
ranked), `method.html`, `challenges.html`, `changelog.html`, `data.html` (audit downloads +
reproduce), `about.html`, `press.html`, `share.html`. Corpus counts live in the data, not in
this document: `data/seeds/*.json` is the single source (610 books / 269 papers as of
pilot-v0.2; the pages compute their own numbers).

---

## Security posture and guardrails

The static threat model: an attacker's only lever is data that reaches the generated HTML
(titles, descriptions, names, URLs), plus the browser delivery surface. Each guardrail below
is enforced by `scripts/static-gate.sh`.

- **[S0] Syntax.** All Python modules compile (`py_compile`).
- **[S1] Test suite.** The full pytest suite is green (schema, scorer, ER, harvest, release,
  site, security).
- **[S2] No commercial code.** No ad / affiliate / tracker code signatures in `src/` or
  `site/` (`scripts/guard_no_trackers.sh`).
- **[S3] No em-dashes** in any generated HTML (house style).
- **[S4] Link integrity.** Zero broken internal links across the generated site.
- **[S5] Strict CSP + security headers.** `site/_headers` sets `default-src 'none'` with no
  `unsafe-inline` / `unsafe-eval`, plus `frame-ancestors 'none'`, `object-src 'none'`,
  X-Content-Type-Options, Referrer-Policy, X-Frame-Options, COOP, CORP, Permissions-Policy, HSTS.
- **[S6] No inline executable script or style.** All CSS/JS is external `'self'`. The only inline
  `<script>` permitted is the site-wide `application/ld+json` SEO block, and only because its sha256
  is pinned in the CSP `script-src` (never `unsafe-inline`); a test fails the build on any other
  inline script or any unpinned JSON-LD.
- **[S7] No third-party requests.** Fonts and assets are self-hosted; no Google Fonts, CDN, or
  tracker origin appears in any page or stylesheet.
- **[S8] Output safety.** Every data field is HTML-escaped at the render boundary (`esc`,
  `quote=True`); data-derived hrefs are scheme-sanitized (`safe_url`: only http/https/mailto,
  else `#`). Adversarial XSS fixtures assert hostile titles, descriptions, and `javascript:`
  URLs cannot become markup or script.
- **[S9] Deterministic reproduction.** `release --verify` rebuilds the release and asserts a
  bit-identical `corpus_hash`.
- **[S10] Self-contained audit bundle.** `audit-bundle.zip` carries code + weights + pinned
  data + reproduce script; it rebuilds the release offline with no repo.
- **[S11] Clean deployable.** Only static assets ship in `site/`; no `.py`, `.env`, secrets,
  or build artifacts.
- **[S12] Architecture drift.** Two-directional: every `[S##]` named here must appear in the
  gate script, and every `[S##]` the gate checks must be documented here; the gate fails if
  the two diverge in either direction.
- **[S13] Accessibility.** A full axe-core pass across all page types is clean (0 violations).
  A static lint keeps the prerequisites from regressing in CI without a browser: every page
  declares a language, has exactly one h1, gives every image alt text, and never skips a
  heading level. Body links are underlined (distinguishable without color) and footer text
  meets the contrast threshold.
- **[S14] No committed secrets.** The repo is public and archived permanently on Zenodo, so a
  leaked key would be undeletable. `guard_no_secrets.sh` scans every tracked file for real
  credential signatures (provider key prefixes with length anchors, private-key blocks); the gate
  fails on a hit. Placeholders and example values do not trip it.
- **[S15] Frozen releases are byte-immutable.** Every version pinned in
  `data/releases/FROZEN.json` must still hash to its recorded tree sha256
  (`release --check-frozen`); `release.build()` and `bundle()` refuse a frozen version, the
  registry is append-only, and the test suite builds only scratch versions. Corrections to a
  frozen release are a new version or a changelog entry, never an edit (rule 11). The one
  historical exception is recorded in `data/releases/pilot-v0.1/ADDENDUM.md`.
- **[S16] Scoring changes carry a changelog entry.** Any commit that touches `scenarios.yaml`
  or `src/canon/score.py` must touch `CHANGELOG.md` in the same commit (rule 10); the gate also
  refuses a working tree that modifies those files without a changelog edit. Enforced from the
  baseline commit 9d46b74 onward; the one prior violation (8845a59) is recorded retroactively
  in the changelog.
- **[S17] Evidence currency.** The validation registers cover the corpus exactly as shipped
  (every paper and book id has a register row, none are stale), no voice bio is published from
  an unchecked source (register status must be VERIFIED / CORRECTED / SOURCE-UPGRADED), every
  verbatim abstract carries its source, retrieved date, license note, and a source URL or a
  declared source-URL gap, and the LICENSE-DATA carve-out for quoted abstracts stays in place.
- **[S19] Size discipline.** The style rule "a new contributor understands any file in 10
  minutes" is enforced mechanically (`scripts/check_sizes.py`): no module in `src/canon/`
  over 600 lines, no function over 60. Long prose lives in module-level constants, not code.
- **[S20] Toolchain pinning.** `requirements.lock` is the single dependency source:
  `make install`, CI, and the audit bundle's reproduce harness all install from it, and the
  gate fails if the running environment's versions drift from the lock
  (`scripts/check_lock.py`). Reproducibility covers the tools, not just the data.
- **[S18] Hostile-fixture render safety.** Beyond [S8]'s checks on real output, adversarial
  fixtures (attribute-breaking quotes, script tags, `javascript:` URLs) are injected through
  every page renderer and the output is asserted breakout-free; `safe_url()` results must be
  `esc()`-wrapped in attributes (safe_url passes quotes through by design); titles escape
  exactly once; `raw.read()` raises on evidence whose bytes no longer match the harvest-time
  manifest sha256; and raw record names reject path separators. Verbatim quotations keep
  their em-dashes ([S3] scopes to generated copy, never to the authors' own words).

## Non-functional requirements

Reproducible builds; static-first; full Unicode (CJK titles render via system fallback;
romanization is a declared gap); core reading works with no JavaScript (filtering enhances);
no browser storage (no localStorage / sessionStorage / cookies); the corpus is consumable as
open JSON and CSV without the site.

## Funding and independence

No advertising, no affiliate links, no sponsored placement, no paid inclusion, ever.
CI-enforced (`[S2]`). Apparens-authored works carry `conflict_flag: true`, surfaced in the data
and on the page, subject to the same rules with no exemption and no boost (books carry no
metrics yet, so no book, theirs included, is scored).
