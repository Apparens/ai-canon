#!/usr/bin/env bash
# [S14] No committed secrets.
#
# This repo is PUBLIC on GitHub and archived PERMANENTLY on Zenodo (a release
# snapshot cannot be deleted), so a leaked credential would be undeletable.
# Scan every tracked file for real credential signatures. The length anchors
# (16+ chars after a provider prefix) mean placeholders like "sk_live_..." in a
# runbook or "whsec_replace_me" in an example do NOT trip the guard; only
# real-looking keys do.
set -uo pipefail
cd "$(dirname "$0")/.."

PATTERN='sk_live_[0-9A-Za-z]{16}|rk_live_[0-9A-Za-z]{16}|sk_test_[0-9A-Za-z]{16}|whsec_[0-9A-Za-z]{20}|AKIA[0-9A-Z]{16}|gh[pousr]_[0-9A-Za-z]{36}|xox[baprs]-[0-9A-Za-z-]{12,}|AIza[0-9A-Za-z_-]{35}|sk-ant-[0-9A-Za-z_-]{20}|sk-proj-[0-9A-Za-z_-]{20}|eyJ[0-9A-Za-z_-]{20,}\.eyJ[0-9A-Za-z_-]{20,}\.|[Bb]earer [0-9A-Za-z_.~+/-]{25,}|https?://[^/@ ]+:[^/@ ]{8,}@|-----BEGIN [A-Z ]*PRIVATE KEY-----'

# git grep scans only tracked files (exactly what gets pushed + archived);
# exclude this guard so its own PATTERN string cannot self-match.
if hits=$(git grep -EnI "$PATTERN" -- . ":(exclude)scripts/guard_no_secrets.sh" 2>/dev/null); then
  echo "FAIL: possible secret in a tracked file (repo is public + Zenodo-permanent):"
  printf '%s\n' "$hits" | head -20
  echo "If this is a placeholder/test value, lengthen/rename it; never commit a real key."
  exit 1
fi

# The gitignored pilot-frontier/ workspace never ships, but if it is ever
# un-ignored it enters the public repo unaudited: scan it too when present.
if [ -d pilot-frontier ]; then
  if hits=$(grep -REnI "$PATTERN" pilot-frontier --include='*.py' --include='*.json' --include='*.md' 2>/dev/null); then
    echo "FAIL: possible secret in pilot-frontier/ (would leak if the dir is ever committed):"
    printf '%s\n' "$hits" | head -10
    exit 1
  fi
fi
echo "OK: no secret signatures in tracked files (pilot-frontier scanned when present)."
