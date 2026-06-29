#!/usr/bin/env bash
# Rule 1: no advertising, affiliate, or tracking code may exist in the repo.
#
# This greps for CODE signatures of trackers/ad networks/affiliate tags — script
# sources and JS calls — NOT the words "ads"/"affiliates"/"sponsors", which
# legitimately appear in the site's prose as a PROMISE not to use them. Searching
# the prose would punish the very commitment it states.
set -euo pipefail

ROOTS=(src site)

# Known tracker / ad-network / affiliate-tag code signatures.
PATTERN='googletagmanager|google-analytics\.com|gtag\(|analytics\.js|fbevents|fbq\(|doubleclick\.net|adsbygoogle|amazon-adsystem|hotjar|mixpanel|segment\.com/analytics|affiliate[_-]?id|partner[_-]?tag'

hits=""
for root in "${ROOTS[@]}"; do
  [ -e "$root" ] || continue
  if found=$(grep -REn "$PATTERN" "$root" 2>/dev/null); then
    hits="$hits$found"$'\n'
  fi
done

if [ -n "${hits// /}" ] && [ -n "$(printf '%s' "$hits" | tr -d '[:space:]')" ]; then
  echo "FAIL: ad/affiliate/tracker code signature found (rule 1):"
  printf '%s\n' "$hits"
  exit 1
fi

echo "OK: no ad/affiliate/tracker code signatures in ${ROOTS[*]}."
