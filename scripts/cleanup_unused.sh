#!/usr/bin/env bash
# Repo ki safai. DEFAULT = DRY RUN (kuch delete nahi hota).
# Asli delete ke liye: ./scripts/cleanup_unused.sh --apply
set -euo pipefail
cd "$(dirname "$0")/.."

APPLY=0
if [ "${1:-}" = "--apply" ]; then APPLY=1; fi

TARGETS=(
  "Strategy-Backtesting-v3.zip"
  "Strategy-Backtesting-v4.zip"
  "Strategy-Backtesting-v8.zip"
  "fyers_hub.zip"
  "greeks_manifests.zip"
  "greeks_plugin.zip"
  "gts_lab_strategies (1).zip"
  "gts_lab_strategies (2).zip"
  "archive/gts_quant_lab.zip"
  "archive/quant_stat_arb_framework.zip"
  "archive/bootstrap-5.py"
  "archive/bootstrap (4).py"
)

for t in "${TARGETS[@]}"; do
  if [ -e "$t" ]; then
    if [ $APPLY -eq 1 ]; then
      rm -f -- "$t" && echo "removed: $t"
    else
      echo "would remove: $t"
    fi
  fi
done

while IFS= read -r link; do
  if [ $APPLY -eq 1 ]; then
    rm -f -- "$link" && echo "removed broken symlink: $link"
  else
    echo "would remove broken symlink: $link"
  fi
done < <(find . -xtype l -not -path './.git/*')

echo "NOTE: canonical generator scripts/bootstrap.py hai; purane copies archive/ me hain."
if [ $APPLY -ne 1 ]; then
  echo "Dry run tha. Asli delete ke liye: $0 --apply"
fi
