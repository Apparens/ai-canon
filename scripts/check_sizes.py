"""[S19] Size discipline: a new contributor understands any file in 10 minutes.

Enforces the CLAUDE.md style rule mechanically over src/canon/:
  * no module longer than MAX_MODULE lines
  * no function/method longer than MAX_FUNC lines (decorators excluded;
    module-level string constants are deliberately NOT counted as code)

Zero dependencies (stdlib ast), deterministic, exit 1 on any violation.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "canon"
MAX_MODULE = 600
MAX_FUNC = 60


def check() -> list[str]:
    problems: list[str] = []
    for py in sorted(SRC.rglob("*.py")):
        rel = py.relative_to(SRC.parents[1])
        text = py.read_text("utf-8")
        n_lines = text.count("\n") + 1
        if n_lines > MAX_MODULE:
            problems.append(f"{rel}: {n_lines} lines (max {MAX_MODULE})")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                span = node.end_lineno - node.lineno + 1
                if span > MAX_FUNC:
                    problems.append(
                        f"{rel}:{node.lineno} {node.name}() is {span} lines (max {MAX_FUNC})"
                    )
    return problems


if __name__ == "__main__":
    bad = check()
    for b in bad:
        print(b)
    print(f"[S19] {'OK: size discipline holds' if not bad else f'{len(bad)} violations'}")
    sys.exit(1 if bad else 0)
