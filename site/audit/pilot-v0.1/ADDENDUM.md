# Addendum to pilot-v0.1 (recorded 2026-07-02)

This release was modified after its creation, in violation of the append-only
promise (rule 11). This addendum is the honest record of what happened. The
files are kept exactly as they now stand; nothing was deleted or rewritten to
hide the trace, and the original bytes remain recoverable from git history
(the parent of commit 8845a59).

## What happened

- 2026-06-29 (commit 8845a59): the second scoring signal was recomputed as
  `readership_persistence` (the number of distinct years a work keeps being
  cited, a longevity proxy), replacing `sustained_readership` (a recent-citation
  sum, a recency proxy wearing a longevity name). The change was right on the
  merits, but it regenerated this release's `breakdowns/` and `REPRODUCE.md`
  in place, and landed without a CHANGELOG entry (rule 10).
- 2026-06-30 (commit 65a3dfe): `audit-bundle.zip` was regenerated, picking up
  post-launch seed data.

## Current state (verified 2026-07-02)

- The audit bundle is self-consistent: extracting `audit-bundle.zip` and
  running `bash reproduce.sh` rebuilds this release offline and reports
  corpus_hash MATCH (`ecaac0049c25baa9...`).
- `python -m canon.release --verify --version pilot-v0.1` from the live repo
  reports MISMATCH. That is expected for any superseded release: `--verify`
  rebuilds from the current corpus, which has legitimately grown since. The
  reproducibility claim for a superseded release is carried by its bundle.

## What changed as a consequence

- `data/releases/FROZEN.json` now pins every released version to a tree hash.
  Gate check [S15] fails if a frozen release changes by a single byte, and
  `release.build()` / `bundle()` refuse a frozen version outright.
- Gate check [S16] fails any commit that touches `scenarios.yaml` or
  `src/canon/score.py` without a CHANGELOG entry in the same commit.
- The test suite no longer rebuilds the published release in place, which was
  the mechanism that silently rewrote this one.
