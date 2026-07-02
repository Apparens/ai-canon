"""[S20] Toolchain pinning: the running environment matches requirements.lock.

The lock is the single dependency source (Makefile, CI, and the audit bundle all
install from it); this check catches the drift case where someone pip-installs
ad hoc and the "reproducible" build quietly stops matching the pinned toolchain.
"""
from __future__ import annotations

import importlib.metadata as im
import sys
from pathlib import Path

LOCK = Path(__file__).resolve().parents[1] / "requirements.lock"
# The direct dependencies; transitive pins matter at install time, not here.
CHECK = ("pydantic", "openpyxl", "PyYAML", "pytest", "pillow")


def main() -> int:
    lock: dict[str, str] = {}
    for line in LOCK.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "==" in line:
            name, ver = line.split("==")
            lock[name.lower().replace("_", "-")] = ver
    bad = []
    for name in CHECK:
        key = name.lower().replace("_", "-")
        try:
            installed = im.version(name)
        except im.PackageNotFoundError:
            bad.append(f"{name}: pinned in lock but not installed")
            continue
        if lock.get(key) != installed:
            bad.append(f"{name}: installed {installed} != lock {lock.get(key)}")
    for b in bad:
        print(b)
    print(f"[S20] {'OK: toolchain matches requirements.lock' if not bad else f'{len(bad)} drifts'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
