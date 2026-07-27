#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
solver="${CADICAL:-cadical}"

mkdir -p "$root/artifacts/proofs"
python3 "$root/scripts/generate.py"

solve() {
  name="$1"
  set +e
  "$solver" --quiet --no-binary \
    "$root/artifacts/cnf/$name.cnf" \
    "$root/artifacts/proofs/$name.drat" \
    >"$root/artifacts/proofs/$name.solver.txt"
  status=$?
  set -e
  if [[ $status -ne 20 ]]; then
    echo "solver did not report UNSAT for $name (exit $status)" >&2
    exit 1
  fi
}

for bound in 0 1 2; do
  solve "period2-pop-le-$bound"
done
solve "goe45-predecessor"
python3 "$root/scripts/generate.py"
"$root/scripts/verify_proofs.sh"
