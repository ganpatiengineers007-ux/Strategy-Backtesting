#!/usr/bin/env bash
# Naye machine par: ./scripts/setup_truemax.sh
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
. .venv/bin/activate
pip install -q -U pip pytest
./scripts/validate_repo.sh
python -m cli.main demo
