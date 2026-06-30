# Reproduce pilot-v0.2

This release rebuilds deterministically from the repository.

```bash
make install
make assemble          # derive metrics from the write-once raw cache
make release           # rebuild this release
make verify-release    # assert corpus_hash + rankings are bit-identical
```

- corpus_hash: `c379e0a8cbcf64ad88131a6e1588035b66f40961e86db30dd938e2cbba922769`
- method_version: `0.1-pilot`
- date (metadata, not hashed): 2026-06-30

If `make verify-release` reports MISMATCH, the release is defective. File a challenge
to office@apparens.nl.
