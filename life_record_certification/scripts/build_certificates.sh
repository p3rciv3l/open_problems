#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
solver="${CADICAL:-cadical}"

python3 "$root/scripts/generate.py"
for bound in 0 1 2; do
  set +e
  "$solver" --quiet --no-binary \
    "$root/artifacts/cnf/period2-pop-le-$bound.cnf" \
    "$root/artifacts/proofs/period2-pop-le-$bound.drat" \
    >"$root/artifacts/proofs/period2-pop-le-$bound.solver.txt"
  status=$?
  set -e
  if [[ $status -ne 20 ]]; then
    echo "solver did not report UNSAT for bound $bound (exit $status)" >&2
    exit 1
  fi
done
python3 "$root/scripts/generate.py"
"$root/scripts/verify_proofs.sh"
