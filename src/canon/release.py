"""CAN-15 / CAN-16 — release builder + audit package.

A release is a frozen, reproducible snapshot under data/releases/<version>/:

  * release.json   — governance record (version, date, corpus_hash, method_version,
                     changelog_ref) + scope and per-scenario divergence summary
  * rankings/      — Top-N per (domain, scenario), each row linking to its breakdown
  * breakdowns/    — the full trust surface per ranked work (every metric, source,
                     retrieved_at, confidence, provenance_url, weight, penalties)
  * coverage.json  — declared gaps copied from data/resolved
  * REPRODUCE.md   — the one command that rebuilds and re-verifies this release

`corpus_hash` is a sha256 over the canonical serialization of the exact inputs
(works in scope + metrics + weights). `build()` then `verify()` rebuilds from the
same inputs and asserts the hash and rankings are bit-identical — if they are not,
the release is defective (rule 3). The release DATE is metadata and does not enter
the hash, so re-running on another day still reproduces the same corpus_hash.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from . import METHOD_VERSION, RELEASE_VERSION
from . import schema
from .score import (
    load_corpus_metrics,
    load_corpus_works,
    load_scenarios,
    rank_within_domain,
    to_json,
)

_ROOT = Path(__file__).resolve().parents[2]
RELEASES = _ROOT / "data" / "releases"
RESOLVED = _ROOT / "data" / "resolved"
FROZEN_REGISTRY = RELEASES / "FROZEN.json"
TOP_N = 50
DEFAULT_VERSION = RELEASE_VERSION  # single source: canon/__init__.py
DEFAULT_DATE = "2026-07-02"  # metadata only; not part of corpus_hash


class ReleaseFrozenError(RuntimeError):
    """Raised when build()/bundle() targets a version pinned in FROZEN.json (rule 11)."""


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _load_frozen() -> dict:
    if not FROZEN_REGISTRY.exists():
        return {}
    return json.loads(FROZEN_REGISTRY.read_text("utf-8"))


def _refuse_if_frozen(version: str) -> None:
    if version in _load_frozen():
        raise ReleaseFrozenError(
            f"{version} is frozen in data/releases/FROZEN.json; releases are "
            "append-only (rule 11): bump the version instead of rebuilding"
        )


def _is_sync_junk(name: str) -> bool:
    """Cloud-sync duplicate copies ("paper-0001 2.json"). No release artifact
    ever carries a space in its filename, so a space means the file is not ours;
    hashing or bundling it would make the pin machine-specific."""
    return " " in name


def _tree_sha256(version: str) -> str:
    """One hash over every byte of a release dir (sorted, path-labelled)."""
    rel_dir = RELEASES / version
    lines = "".join(
        f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(rel_dir).as_posix()}\n"
        for f in sorted(rel_dir.rglob("*"))
        if f.is_file() and not _is_sync_junk(f.name)
    )
    return _sha256(lines)


def freeze(version: str, date: str) -> None:
    """Pin a released version to its current bytes. Append-only: no re-freeze."""
    frozen = _load_frozen()
    if version in frozen:
        raise ReleaseFrozenError(f"{version} is already frozen; the registry is append-only")
    if not (RELEASES / version / "release.json").exists():
        raise FileNotFoundError(f"no release.json under data/releases/{version}/")
    frozen[version] = {"frozen_on": date, "tree_sha256": _tree_sha256(version)}
    FROZEN_REGISTRY.write_text(
        json.dumps(frozen, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"frozen {version}: tree {frozen[version]['tree_sha256'][:16]}…")


def check_frozen() -> bool:
    """[S15] Every frozen release must still hash to its registered tree sha256."""
    ok = True
    for version, entry in sorted(_load_frozen().items()):
        if not (RELEASES / version).is_dir():
            print(f"frozen {version}: MISSING (dir deleted)")
            ok = False
            continue
        match = _tree_sha256(version) == entry["tree_sha256"]
        print(f"frozen {version}: tree {'MATCH' if match else 'MISMATCH'} ({entry['tree_sha256'][:16]}…)")
        ok = ok and match
    return ok


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _domains_with_evidence(metrics_by_work: dict) -> dict[str, list]:
    """Map work_type -> works that have at least one metric, by domain."""
    out: dict[str, list] = {}
    for wt in ("paper", "book"):
        works = [w for w in load_corpus_works(wt) if w.id in metrics_by_work]
        if works:
            out[wt] = works
    return out


def _corpus_hash(domains: dict, metrics_by_work: dict, scenarios_doc: dict) -> str:
    works_blob = sorted(
        (w.id, w.work_type, w.canonical_title) for ws in domains.values() for w in ws
    )
    # Since pilot-v0.3 the hash covers the FULL provenance of every metric row
    # (rule 2): altering a retrieved_at, confidence, or license_note after the
    # fact fails verification exactly like altering the value would.
    metrics_blob = sorted(
        (m.work_id, m.metric_name, m.value, m.source, m.provenance_url,
         m.retrieved_at.isoformat(), m.confidence, m.license_note)
        for ms in metrics_by_work.values()
        for m in ms
    )
    weights_blob = scenarios_doc["scenarios"]
    return _sha256(_canonical([works_blob, metrics_blob, weights_blob]))


def _build_payload(version: str, date: str) -> dict:
    scenarios_doc = load_scenarios()
    metrics_by_work = load_corpus_metrics()
    domains = _domains_with_evidence(metrics_by_work)
    scenario_names = sorted(scenarios_doc["scenarios"])

    rankings: dict[str, list] = {}
    breakdowns: dict[str, dict] = {}
    for domain, works in sorted(domains.items()):
        for scenario in scenario_names:
            # rank_within_domain already returns full per-work breakdown rows.
            rows = rank_within_domain(works, metrics_by_work, scenario, scenarios_doc)
            key = f"{domain}__{scenario}"
            rankings[key] = rows[:TOP_N]
            # The published ranking is the Top-N (the Canon-50), but every work that
            # has harvested evidence gets its full trust-surface breakdown, so a scored
            # work outside the Top-N still links to its real evidence and its real rank,
            # never shown as "no evidence yet". Breakdowns are derived output and do not
            # enter corpus_hash.
            for row in rows:
                breakdowns.setdefault(row["work_id"], {})[scenario] = row

    divergence = _divergence(rankings, domains, scenario_names)
    corpus_hash = _corpus_hash(domains, metrics_by_work, scenarios_doc)
    record = {
        "version": version,
        "date": date,
        "corpus_hash": corpus_hash,
        "method_version": METHOD_VERSION,
        "changelog_ref": "CHANGELOG.md#pilot-v03",
        "scope": {
            "domains": {d: len(ws) for d, ws in sorted(domains.items())},
            "scenarios": scenario_names,
            "top_n": TOP_N,
            "note": "Domains without harvested metrics are omitted, not zero-filled. "
            "Books carry no metrics yet (harvesting deferred); this pilot ranks papers only.",
        },
        "divergence": divergence,
    }
    # The governance record must satisfy the frozen ontology's Release model
    # (rule: governance records are typed records, not ad-hoc dicts). We write
    # the original dict, not the model dump, so serialization stays byte-stable.
    schema.Release(**record)
    return {
        "release": record,
        "rankings": rankings,
        "breakdowns": breakdowns,
        "corpus_hash": corpus_hash,
    }


def _divergence(rankings: dict, domains: dict, scenario_names: list) -> dict:
    """For each domain, how much do the scenario Top-N orderings differ?"""
    out = {}
    for domain in sorted(domains):
        orders = {
            s: [r["work_id"] for r in rankings[f"{domain}__{s}"]] for s in scenario_names
        }
        base = orders[scenario_names[0]]
        identical = all(orders[s] == base for s in scenario_names)
        out[domain] = {
            "identical_ordering_across_scenarios": identical,
            "note": (
                "Scenarios produce the SAME ordering because only one metric "
                "(citation_count) is present; ordering will diverge once "
                "library_holdings / syllabus_adoptions / readership_persistence are "
                "harvested. This is a declared limitation, not a bug."
                if identical
                else "Scenario orderings differ: multi-metric divergence observed."
            ),
        }
    return out


def build(version: str = DEFAULT_VERSION, date: str = DEFAULT_DATE, *,
          root: Path | None = None) -> dict:
    _refuse_if_frozen(version)
    payload = _build_payload(version, date)
    out_dir = (root or RELEASES) / version
    (out_dir / "rankings").mkdir(parents=True, exist_ok=True)
    (out_dir / "breakdowns").mkdir(parents=True, exist_ok=True)
    # A release is a clean snapshot, not an accumulation: clear prior rankings and
    # breakdowns so a rebuild on changed evidence cannot leave stale files behind.
    for stale in (out_dir / "rankings").glob("*.json"):
        stale.unlink()
    for stale in (out_dir / "breakdowns").glob("*.json"):
        stale.unlink()

    (out_dir / "release.json").write_text(
        json.dumps(payload["release"], sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for key, rows in payload["rankings"].items():
        (out_dir / "rankings" / f"{key}.json").write_text(to_json(rows) + "\n", encoding="utf-8")
    for work_id, per_scenario in payload["breakdowns"].items():
        (out_dir / "breakdowns" / f"{work_id}.json").write_text(
            json.dumps(per_scenario, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if (RESOLVED / "coverage.json").exists():
        (out_dir / "coverage.json").write_text(
            (RESOLVED / "coverage.json").read_text("utf-8"), encoding="utf-8"
        )
    (out_dir / "REPRODUCE.md").write_text(_reproduce_md(payload["release"]), encoding="utf-8")
    bundle(version, root=root)  # self-contained, offline, reproducible audit archive
    print(json.dumps({"built": version, "corpus_hash": payload["corpus_hash"],
                      "rankings": list(payload["rankings"]),
                      "breakdowns": len(payload["breakdowns"])}, indent=2))
    return payload


def verify(version: str = DEFAULT_VERSION, *, root: Path | None = None) -> bool:
    """Rebuild from inputs and assert the committed release is bit-identical.

    Only meaningful for the release whose inputs are the CURRENT corpus (the
    latest). A superseded release verifies via its own audit-bundle.zip, which
    pins the data snapshot it was built from.
    """
    from . import raw

    bad = raw.verify_manifest() if raw.RAW_DIR.exists() else []
    if bad:
        for b in bad[:10]:
            print(f"raw evidence integrity: {b}")
        print(f"verify {version}: raw cache FAILED integrity ({len(bad)} records)")
        return False
    out_dir = (root or RELEASES) / version
    committed = json.loads((out_dir / "release.json").read_text("utf-8"))
    rebuilt = _build_payload(version, committed["date"])
    ok = rebuilt["corpus_hash"] == committed["corpus_hash"]
    # also re-check each ranking file matches
    for key, rows in rebuilt["rankings"].items():
        on_disk = (out_dir / "rankings" / f"{key}.json").read_text("utf-8").rstrip("\n")
        if to_json(rows) != on_disk:
            ok = False
    # ... and every breakdown (the trust surface itself must be tamper-evident,
    # not just the headline hash) and the declared-gaps record.
    for work_id, per_scenario in rebuilt["breakdowns"].items():
        bpath = out_dir / "breakdowns" / f"{work_id}.json"
        rebuilt_text = json.dumps(per_scenario, sort_keys=True, ensure_ascii=False, indent=2)
        if not bpath.exists() or bpath.read_text("utf-8").rstrip("\n") != rebuilt_text:
            print(f"verify {version}: breakdown mismatch {work_id}")
            ok = False
            break
    cov = RESOLVED / "coverage.json"
    cov_disk = out_dir / "coverage.json"
    if cov.exists() and (not cov_disk.exists() or cov.read_text("utf-8") != cov_disk.read_text("utf-8")):
        print(f"verify {version}: coverage.json mismatch")
        ok = False
    print(f"verify {version}: corpus_hash {'MATCH' if ok else 'MISMATCH'} ({committed['corpus_hash'][:16]}…)")
    return ok


def _reproduce_md(record: dict) -> str:
    return f"""# Reproduce {record['version']}

This release rebuilds deterministically from the repository.

```bash
make install
make assemble          # derive metrics from the write-once raw cache
make release           # rebuild this release
make verify-release    # assert corpus_hash + rankings are bit-identical
```

- corpus_hash: `{record['corpus_hash']}`
- method_version: `{record['method_version']}`
- date (metadata, not hashed): {record['date']}

If `make verify-release` reports MISMATCH, the release is defective. File a challenge
to office@apparens.nl.

Once a newer release exists, the live corpus has moved on and the commands above
no longer apply to this version: verify a superseded release from its own
`audit-bundle.zip` (`bash reproduce.sh`), which pins the exact data snapshot.
"""


def _bundle_files(version: str, rel_dir: Path) -> dict[str, bytes]:
    """Collect the audit bundle's payload: code, weights, pinned data, release
    outputs, and the reproduce harness, keyed by archive name."""
    files: dict[str, bytes] = {}

    def add(arcname: str, data: bytes):
        files[arcname] = data

    # 1. pipeline code
    src = _ROOT / "src" / "canon"
    for py in sorted(src.rglob("*.py")):
        add(f"src/canon/{py.relative_to(src).as_posix()}", py.read_bytes())
    # 2. weights + 3. pinned data snapshot
    add("scenarios.yaml", (_ROOT / "scenarios.yaml").read_bytes())
    for name in ("papers.json", "books.json", "persons.json", "orgs.json", "platforms.json"):
        add(f"data/seeds/{name}", (_ROOT / "data" / "seeds" / name).read_bytes())
    for name in ("metrics.json", "coverage.json"):
        p = RESOLVED / name
        if p.exists():
            add(f"data/resolved/{name}", p.read_bytes())
    # 4. the release outputs being verified (everything except a prior bundle)
    for f in sorted(rel_dir.rglob("*")):
        if f.is_file() and f.name != "audit-bundle.zip" and not _is_sync_junk(f.name):
            add(f"data/releases/{version}/{f.relative_to(rel_dir).as_posix()}", f.read_bytes())
    # 5. reproduce harness (pinned: the bundle must rebuild with the exact
    # toolchain of the release, not whatever PyPI serves later)
    add("requirements.txt", (_ROOT / "requirements.lock").read_bytes())
    add("reproduce.sh",
        ("#!/usr/bin/env bash\nset -euo pipefail\n"
         "python3 -m venv .venv\n"
         '.venv/bin/pip install -q -r requirements.txt\n'
         f'PYTHONPATH=src .venv/bin/python -m canon.release --verify --version {version}\n'
         "echo 'If the line above says MATCH, you rebuilt the release exactly.'\n").encode())
    add("README.md",
        (f"# The AI Canon audit bundle: {version}\n\n"
         "Self-contained and offline. Rebuild this release and verify it is bit-identical:\n\n"
         "    bash reproduce.sh\n\n"
         "Contents: the pipeline code (src/canon), the weights (scenarios.yaml), the pinned data\n"
         "snapshot (data/seeds + data/resolved), and the release outputs (data/releases). No network,\n"
         "no external repo, no time dependence. A MISMATCH means the release is defective.\n").encode())
    # manifest of sha256 over every payload file
    manifest = "".join(
        f"{hashlib.sha256(files[k]).hexdigest()}  {k}\n" for k in sorted(files)
    )
    add("MANIFEST.sha256", manifest.encode())
    return files


def bundle(version: str = DEFAULT_VERSION, *, root: Path | None = None) -> Path:
    """Write a self-contained, offline, time-invariant audit archive.

    A stranger with only `audit-bundle.zip` can rebuild this release with one
    command and no network and no repo: it carries the pipeline code, the weights,
    the pinned data snapshot (seeds + assembled metrics), the release outputs, and
    a reproduce script. The zip is built deterministically (sorted entries, fixed
    timestamps) so it is itself reproducible.
    """
    import zipfile

    _refuse_if_frozen(version)
    rel_dir = (root or RELEASES) / version
    files = _bundle_files(version, rel_dir)

    out = rel_dir / "audit-bundle.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for arcname in sorted(files):
            info = zipfile.ZipInfo(arcname, date_time=(2026, 6, 29, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[arcname])
    print(f"bundle {version}: {out} ({len(files)} files)")
    return out


def _main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Build/verify/freeze an AI Canon release")
    p.add_argument("--version", default=DEFAULT_VERSION)
    p.add_argument("--verify", action="store_true")
    p.add_argument("--freeze", action="store_true",
                   help="pin --version to its current bytes in FROZEN.json (append-only)")
    p.add_argument("--check-frozen", action="store_true",
                   help="[S15] assert every frozen release is byte-identical to its pin")
    p.add_argument("--date", default=None, help="freeze date (YYYY-MM-DD)")
    args = p.parse_args(argv)
    if args.check_frozen:
        return 0 if check_frozen() else 1
    if args.freeze:
        import datetime

        freeze(args.version, args.date or datetime.date.today().isoformat())
        return 0
    if args.verify:
        return 0 if verify(args.version) else 1
    build(args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
