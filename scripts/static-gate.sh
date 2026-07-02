#!/usr/bin/env bash
# The AI Canon ship gate. Every [S##] guardrail in ARCHITECTURE.md has a check
# here; [S12] fails the gate if the two diverge IN EITHER DIRECTION (a documented
# guardrail with no check, or a check the doc does not explain).
# Run: bash scripts/static-gate.sh   (uses .venv if present, else python3)
set -uo pipefail
cd "$(dirname "$0")/.."

PY="${PY:-}"; [ -z "$PY" ] && { [ -x .venv/bin/python ] && PY=.venv/bin/python || PY=python3; }
fail=0
run(){ local label="$1"; shift; printf '── %s\n' "$label"; if "$@" >/tmp/canon_gate.log 2>&1; then echo "   PASS"; else echo "   FAIL"; sed 's/^/   | /' /tmp/canon_gate.log | tail -8; fail=1; fi; }

run "[S0] python syntax"            bash -c "$PY -m py_compile src/canon/*.py src/canon/harvest/*.py"
# The pytest suite carries the assertions for [S3] em-dashes, [S4] link
# integrity, [S5]/[S6] CSP + inline-script, [S7] third-party requests,
# [S8] output escaping, [S9] deterministic reproduction, [S10] audit bundle,
# and [S13] accessibility; the labels below name what lives where.
run "[S1] test suite (asserts S3 S4 S5 S6 S7 S8 S9 S10 S13)" \
    bash -c "PYTHONPATH=src $PY -m pytest -q"
run "[S2] no ad/affiliate/tracker"  bash scripts/guard_no_trackers.sh
run "[S14] no committed secrets"    bash scripts/guard_no_secrets.sh
run "[S11] clean deployable (no source/secrets/sync-junk in site/)" \
    bash -c '! find site \( -type f \( -name "*.py" -o -name "*.pyc" -o -name ".env" -o -name "*.sqlite*" \) -o -name "* [0-9]*" \) | grep -q .'
run "[S12] architecture drift (two-directional)" bash -c '
  doc=$(grep -oE "\[S[0-9]+\]" ARCHITECTURE.md | sort -u)
  gate=$(grep -oE "\[S[0-9]+\]" scripts/static-gate.sh | sort -u)
  m1=$(comm -23 <(echo "$doc") <(echo "$gate")); m2=$(comm -13 <(echo "$doc") <(echo "$gate"))
  [ -z "$m1" ] || { echo "documented but no gate check: $m1"; exit 1; }
  [ -z "$m2" ] || { echo "gate check undocumented in ARCHITECTURE.md: $m2"; exit 1; }'
run "[S15] frozen releases byte-immutable" \
    bash -c "PYTHONPATH=src $PY -m canon.release --check-frozen"
run "[S16] scoring changes carry a changelog entry" bash -c '
  # rule 10, enforced from baseline 9d46b74; prior history: 3a1faab is the repo
  # genesis, 8845a59 is recorded retroactively in CHANGELOG.md (2026-07-02).
  base=9d46b74; bad=0
  if git rev-parse -q --verify "$base" >/dev/null 2>&1; then
    for c in $(git rev-list "$base"..HEAD); do
      touched=$(git diff-tree --no-commit-id --name-only -r "$c")
      if echo "$touched" | grep -qE "^(scenarios\.yaml|src/canon/score\.py)$"; then
        echo "$touched" | grep -q "^CHANGELOG\.md$" \
          || { echo "commit $c changes scoring without a CHANGELOG.md entry"; bad=1; }
      fi
    done
  fi
  if [ -n "$(git status --porcelain -- scenarios.yaml src/canon/score.py)" ] \
     && [ -z "$(git status --porcelain -- CHANGELOG.md)" ]; then
    echo "working tree modifies scoring files without a CHANGELOG.md edit"; bad=1
  fi
  exit $bad'
run "[S17] evidence currency" \
    bash -c "PYTHONPATH=src $PY -m pytest -q tests/test_evidence.py"
run "[S18] hostile-fixture render safety" \
    bash -c "PYTHONPATH=src $PY -m pytest -q tests/test_render_security.py"
run "[S19] size discipline (10-minute rule)" \
    bash -c "$PY scripts/check_sizes.py"
run "[S20] toolchain pinned to requirements.lock" bash -c "
  grep -q requirements.lock Makefile || { echo 'Makefile does not install from the lock'; exit 1; }
  grep -q requirements.lock .github/workflows/ci.yml || { echo 'CI does not install from the lock'; exit 1; }
  grep -q requirements.lock src/canon/release.py || { echo 'audit bundle does not carry the lock'; exit 1; }
  $PY scripts/check_lock.py"

echo
if [ "$fail" = 0 ]; then echo "GATE PASS"; else echo "GATE FAIL"; exit 1; fi
