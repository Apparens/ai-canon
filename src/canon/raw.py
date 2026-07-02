"""Write-once raw harvest store (CLAUDE.md rule 6).

data/raw/ is the immutable record of what each source returned. Harvesters write
here exactly once per (source, key); a second write with *different* bytes raises
RawImmutableError. Re-writing identical bytes is a no-op so re-runs are safe.

Because the cache is the pinned record, re-running a harvester reads from raw/
and is deterministic — a release can be rebuilt from the audit package without
the network (rule 3). Corrections happen in data/overrides/, never here.

The per-source manifest stores only sha256 + byte length (no timestamps), so the
manifest itself is reproducible.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

# Record names come from seed ids and must stay inside the source dir: plain
# filenames only, no separators (a hostile seed id like "../x" must not escape).
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class RawImmutableError(RuntimeError):
    """Raised on an attempt to overwrite a raw record with different bytes."""


class RawIntegrityError(RuntimeError):
    """Raised when a raw record's bytes no longer match the recorded sha256."""


def _as_bytes(content: str | bytes) -> bytes:
    return content.encode("utf-8") if isinstance(content, str) else content


def _manifest_path(source: str) -> Path:
    return RAW_DIR / source / "manifest.json"


def _load_manifest(source: str) -> dict:
    path = _manifest_path(source)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_manifest(source: str, manifest: dict) -> None:
    path = _manifest_path(source)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {k: manifest[k] for k in sorted(manifest)}
    path.write_text(
        json.dumps(ordered, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def raw_path(source: str, name: str) -> Path:
    if not _NAME_RE.match(name) or not _NAME_RE.match(source):
        raise ValueError(f"invalid raw record name: {source!r}/{name!r}")
    return RAW_DIR / source / name


def exists(source: str, name: str) -> bool:
    return raw_path(source, name).exists()


def read(source: str, name: str) -> bytes | None:
    """Read a raw record, verifying its bytes against the manifest sha256.

    The manifest is not write-only bookkeeping: a record that no longer hashes
    to what was recorded at harvest time is tampered or corrupted evidence, and
    reading it would silently poison everything derived from it."""
    path = raw_path(source, name)
    if not path.exists():
        return None
    data = path.read_bytes()
    recorded = _load_manifest(source).get(name)
    if recorded and hashlib.sha256(data).hexdigest() != recorded["sha256"]:
        raise RawIntegrityError(
            f"raw/{source}/{name} does not match its manifest sha256; "
            "the write-once evidence has been altered"
        )
    return data


def verify_manifest(source: str | None = None) -> list[str]:
    """Check every manifest entry against the bytes on disk.

    Returns the list of bad records ("source/name: reason"); empty means clean.
    Files present without a manifest entry are reported too (unrecorded writes)."""
    problems: list[str] = []
    sources = [source] if source else sorted(
        p.name for p in RAW_DIR.iterdir() if p.is_dir()) if RAW_DIR.exists() else []
    for src in sources:
        manifest = _load_manifest(src)
        for name, entry in sorted(manifest.items()):
            path = RAW_DIR / src / name
            if not path.exists():
                problems.append(f"{src}/{name}: recorded but missing on disk")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                problems.append(f"{src}/{name}: sha256 mismatch")
        for path in sorted((RAW_DIR / src).glob("*")):
            if path.name in ("manifest.json", "README.md") or " " in path.name:
                continue  # sync-junk names are ignored, never trusted
            if path.is_file() and path.name not in manifest:
                problems.append(f"{src}/{path.name}: on disk but not in manifest")
    return problems


def write_once(source: str, name: str, content: str | bytes) -> Path:
    """Write a raw record once. Identical re-write is a no-op; a differing
    re-write raises RawImmutableError (rule 6)."""
    data = _as_bytes(content)
    digest = hashlib.sha256(data).hexdigest()
    path = raw_path(source, name)

    if path.exists():
        existing = hashlib.sha256(path.read_bytes()).hexdigest()
        if existing != digest:
            raise RawImmutableError(
                f"raw/{source}/{name} already exists with different bytes; "
                "raw/ is write-once — make corrections in data/overrides/"
            )
        return path  # identical: idempotent no-op

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    manifest = _load_manifest(source)
    manifest[name] = {"sha256": digest, "bytes": len(data)}
    _save_manifest(source, manifest)
    return path
