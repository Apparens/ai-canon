# Reproduce pilot-v0.3

This release rebuilds deterministically from the repository.

```bash
make install
make assemble          # derive metrics from the write-once raw cache
make release           # rebuild this release
make verify-release    # assert corpus_hash + rankings are bit-identical
```

- corpus_hash: `cd8459a70755fa3e60ed00e83c6dcd4b92ede86e77b0c2d2461bf8e80461e8dc`
- method_version: `0.1-pilot`
- date (metadata, not hashed): 2026-07-02

If `make verify-release` reports MISMATCH, the release is defective. File a challenge
to office@apparens.nl.

Once a newer release exists, the live corpus has moved on and the commands above
no longer apply to this version: verify a superseded release from its own
`audit-bundle.zip` (`bash reproduce.sh`), which pins the exact data snapshot.
