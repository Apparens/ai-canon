# The AI Canon

A free, method-backed reference library for AI knowledge. It ranks **texts, not
people**. It invites correction. It sells nothing.

> Nothing is for sale. Nothing is hidden. Nothing is final.

The **library is the product; the method is the soul.** Any Top-N list is one
*view* over the data. This repository is the reproducible pipeline behind it.
The full strategy, the frozen ontology, and the build plan live in
[`docs/AI_Canon_MASTER_BUILD.md`](docs/AI_Canon_MASTER_BUILD.md); the project
rules are in [`CLAUDE.md`](CLAUDE.md).

## Status

Stage A skeleton + seed import (Sprint 1 + CAN-07). The deterministic scorer,
the frozen ontology, entity-resolution guards, and the full seed corpus are in
place. The pilot Top-50, harvesters, and the public site come in later stages.

## Quickstart

```bash
python3.12 -m venv .venv
make install        # pip install deps into .venv

make ingest         # import the 3 seed workbooks -> data/seeds/*.json
make score          # deterministically score the fixture corpus
make test           # run the constitutional test suite
make guard          # verify no ad/affiliate/tracker code (rule 1)
```

The pipeline is run with `PYTHONPATH=src` (the `Makefile` sets it) rather than an
editable install — `make` targets are the canonical entry points. To run a module
directly: `PYTHONPATH=src .venv/bin/python -m canon.ingest`. `pytest` needs no
`PYTHONPATH` (it reads `pythonpath = src` from `pyproject.toml`).

> Note: `make ingest` reads the source workbooks from `~/Desktop/files` (see the
> paths at the top of `src/canon/ingest.py`); the generated JSON in `data/seeds/`
> is committed, so tests and scoring run without them.

## What the pipeline guarantees

- **Deterministic** — same inputs + scenario → bit-identical ranks.
- **Provenance on every number** — a metric without source/date/url is rejected.
- **No silent imputation** — missing evidence is recorded and penalized by rule.
- **Domains never cross-rank** — a standard is never ranked against a monograph.
- **People are never scored** — context entities have no score field, structurally.
- **No ads, affiliates, or trackers** — enforced in CI.
