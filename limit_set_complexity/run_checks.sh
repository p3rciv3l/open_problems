#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python -m unittest discover -s tests -v
python forcing.py --output result.json
python cap_search.py --min-padding 14 --max-padding 20 --output cap_result.json
