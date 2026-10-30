#!/usr/bin/env bash
# Usage: scripts/run_backtest.sh <strategy_id> <data.csv>
set -euo pipefail
cd "$(dirname "$0")/.."
python -m cli.main run --strategy "$1" --data "$2"
