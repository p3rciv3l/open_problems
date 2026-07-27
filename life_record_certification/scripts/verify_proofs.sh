#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
checker="${DRAT_TRIM:-$root/build/drat-trim}"

if [[ ! -x "$checker" ]]; then
  mkdir -p "$root/build"
  cc -D_GNU_SOURCE -std=c99 -O2 "$root/third_party/drat-trim/drat-trim.c" -o "$checker"
fi

for bound in 0 1 2; do
  "$checker" \
    "$root/artifacts/cnf/period2-pop-le-$bound.cnf" \
    "$root/artifacts/proofs/period2-pop-le-$bound.drat" |
    grep -q "s VERIFIED"
  echo "DRAT OK: bound $bound"
done

"$checker" \
  "$root/artifacts/cnf/goe45-predecessor.cnf" \
  "$root/artifacts/proofs/goe45-predecessor.drat" |
  grep -q "s VERIFIED"
echo "DRAT OK: 45-cell GoE has no predecessor"
