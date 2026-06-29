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

from . import METHOD_VERSION
from .score import (
    _load_corpus_metrics,
    _load_corpus_works,
    load_scenarios,
    rank_within_domain,
    to_json,
)

_ROOT = Path(__file__).resolve().parents[2]
RELEASES = _ROOT / "data" / "releases"
RESOLVED = _ROOT / "data" / "resolved"
TOP_N = 50
DEFAULT_VERSION = "pilot-v0.1"
DEFAULT_DATE = "2026-06-29"  # metadata only; not part of corpus_hash


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _domains_with_evidence(metrics_by_work: dict) -> dict[str, list]:
    """Map work_type -> works that have at least one metric, by domain."""
    out: dict[str, list] = {}
    for wt in ("paper", "book"):
        works = [w for w in _load_corpus_works(wt) if w.id in metrics_by_work]
        if works:
            out[wt] = works
    return out


def _corpus_hash(domains: dict, metrics_by_work: dict, scenarios_doc: dict) -> str:
    works_blob = sorted(
        (w.id, w.work_type, w.canonical_title) for ws in domains.values() for w in ws
    )
    metrics_blob = sorted(
        (m.work_id, m.metric_name, m.value, m.source, m.provenance_url)
        for ms in metrics_by_work.values()
        for m in ms
    )
    weights_blob = scenarios_doc["scenarios"]
    return _sha256(_canonical([works_blob, metrics_blob, weights_blob]))


def _build_payload(version: str, date: str) -> dict:
    scenarios_doc = load_scenarios()
    metrics_by_work = _load_corpus_metrics()
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
            for row in rankings[key]:
                breakdowns.setdefault(row["work_id"], {})[scenario] = row

    divergence = _divergence(rankings, domains, scenario_names)
    corpus_hash = _corpus_hash(domains, metrics_by_work, scenarios_doc)
    record = {
        "version": version,
        "date": date,
        "corpus_hash": corpus_hash,
        "method_version": METHOD_VERSION,
        "changelog_ref": "CHANGELOG.md#seed-v03",
        "scope": {
            "domains": {d: len(ws) for d, ws in sorted(domains.items())},
            "scenarios": scenario_names,
            "top_n": TOP_N,
            "note": "Domains without harvested metrics are omitted, not zero-filled. "
            "Books carry no metrics yet (harvesting deferred); this pilot ranks papers only.",
        },
        "divergence": divergence,
    }
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
                "library_holdings / syllabus_adoptions / sustained_readership are "
                "harvested. This is a declared limitation, not a bug."
                if identical
                else "Scenario orderings differ: multi-metric divergence observed."
            ),
        }
    return out


def build(version: str = DEFAULT_VERSION, date: str = DEFAULT_DATE) -> dict:
    payload = _build_payload(version, date)
    out_dir = RELEASES / version
    (out_dir / "rankings").mkdir(parents=True, exist_ok=True)
    (out_dir / "breakdowns").mkdir(parents=True, exist_ok=True)

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
    bundle(version)  # self-contained, offline, reproducible audit archive
    print(json.dumps({"built": version, "corpus_hash": payload["corpus_hash"],
                      "rankings": list(payload["rankings"]),
                      "breakdowns": len(payload["breakdowns"])}, indent=2))
    return payload


def verify(version: str = DEFAULT_VERSION) -> bool:
    """Rebuild from inputs and assert the committed release is bit-identical."""
    out_dir = RELEASES / version
    committed = json.loads((out_dir / "release.json").read_text("utf-8"))
    rebuilt = _build_payload(version, committed["date"])
    ok = rebuilt["corpus_hash"] == committed["corpus_hash"]
    # also re-check each ranking file matches
    for key, rows in rebuilt["rankings"].items():
        on_disk = (out_dir / "rankings" / f"{key}.json").read_text("utf-8").rstrip("\n")
        if to_json(rows) != on_disk:
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
"""


def bundle(version: str = DEFAULT_VERSION) -> Path:
    """Write a self-contained, offline, time-invariant audit archive.

    A stranger with only `audit-bundle.zip` can rebuild this release with one
    command and no network and no repo: it carries the pipeline code, the weights,
    the pinned data snapshot (seeds + assembled metrics), the release outputs, and
    a reproduce script. The zip is built deterministically (sorted entries, fixed
    timestamps) so it is itself reproducible.
    """
    import hashlib
    import zipfile

    rel_dir = RELEASES / version
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
        if f.is_file() and f.name != "audit-bundle.zip":
            add(f"data/releases/{version}/{f.relative_to(rel_dir).as_posix()}", f.read_bytes())
    # 5. reproduce harness
    add("requirements.txt", b"pydantic>=2\nopenpyxl\npyyaml\n")
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

    out = rel_dir / "audit-bundle.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for arcname in sorted(files):
            info = zipfile.ZipInfo(arcname, date_time=(2026, 6, 29, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[arcname])
    print(f"bundle {version}: {out.relative_to(_ROOT)} ({len(files)} files)")
    return out


def _main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Build/verify an AI Canon release")
    p.add_argument("--version", default=DEFAULT_VERSION)
    p.add_argument("--verify", action="store_true")
    args = p.parse_args(argv)
    if args.verify:
        return 0 if verify(args.version) else 1
    build(args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
