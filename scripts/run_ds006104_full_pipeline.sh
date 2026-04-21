#!/bin/zsh
set -euo pipefail

REPO_ROOT="/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding"
DATASET_ROOT="/Users/samxie/Research/EEG-Voice/openneuro_downloads/ds006104-download"
OUTPUT_ROOT="$REPO_ROOT/exploration_outputs/edf_full_analysis"
LOG_DIR="$REPO_ROOT/exploration_outputs/logs"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_PATH="$LOG_DIR/ds006104_full_pipeline_${TIMESTAMP}.log"

mkdir -p "$LOG_DIR"

echo "[run_ds006104_full_pipeline] Repo root: $REPO_ROOT"
echo "[run_ds006104_full_pipeline] Dataset root: $DATASET_ROOT"
echo "[run_ds006104_full_pipeline] Output root: $OUTPUT_ROOT"
echo "[run_ds006104_full_pipeline] Log file: $LOG_PATH"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[run_ds006104_full_pipeline] python3 not found" >&2
  exit 1
fi

if ! command -v git-annex >/dev/null 2>&1; then
  echo "[run_ds006104_full_pipeline] git-annex not found. Install it first, e.g. brew install git-annex" >&2
  exit 1
fi

if [ ! -d "$DATASET_ROOT" ]; then
  echo "[run_ds006104_full_pipeline] Dataset root does not exist: $DATASET_ROOT" >&2
  exit 1
fi

cd "$REPO_ROOT"

{
  echo "[run_ds006104_full_pipeline] Started at $(date '+%Y-%m-%d %H:%M:%S')"
  echo "[run_ds006104_full_pipeline] Python: $(command -v python3)"
  echo "[run_ds006104_full_pipeline] git-annex: $(command -v git-annex)"
  echo "[run_ds006104_full_pipeline] Running batch download + analysis"

  PYTHONUNBUFFERED=1 python3 scripts/batch_ds006104_pipeline.py \
    --mode all \
    --dataset-root "$DATASET_ROOT" \
    --output-root "$OUTPUT_ROOT" \
    --skip-existing-analysis \
    --continue-on-error

  echo "[run_ds006104_full_pipeline] Finished at $(date '+%Y-%m-%d %H:%M:%S')"
} 2>&1 | tee "$LOG_PATH"

