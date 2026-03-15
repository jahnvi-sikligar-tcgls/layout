#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${VENV_PATH:-$ROOT_DIR/.venv}"
DATASET="${DATASET:-rplan}"
TARGET_SET="${TARGET_SET:-8}"
MODE="${1:-help}"

usage() {
  cat <<EOF
Usage: $(basename "$0") <install|train|sample|designer|help>

Environment variables:
  VENV_PATH   Virtual environment path (default: $ROOT_DIR/.venv)
  DATASET     Dataset name (default: rplan)
  TARGET_SET  Target set id (default: 8)

Examples:
  $(basename "$0") install
  $(basename "$0") train
  $(basename "$0") sample
  $(basename "$0") designer
EOF
}

activate_venv() {
  # shellcheck disable=SC1090
  source "$VENV_PATH/bin/activate"
}

case "$MODE" in
  install)
    python3 -m venv "$VENV_PATH"
    activate_venv
    python -m pip install --upgrade pip
    python -m pip install -r "$ROOT_DIR/requirements.txt"
    ;;
  train)
    activate_venv
    cd "$ROOT_DIR/scripts"
    python image_train.py --dataset "$DATASET" --batch_size 32 --set_name train --target_set "$TARGET_SET"
    ;;
  sample)
    activate_venv
    cd "$ROOT_DIR/scripts"
    python image_sample.py --dataset "$DATASET" --batch_size 32 --set_name eval --target_set "$TARGET_SET" --model_path ckpts/exp/model250000.pt --num_samples 64
    ;;
  designer)
    activate_venv
    cd "$ROOT_DIR/llm"
    python main.py
    ;;
  help|--help|-h)
    usage
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    usage
    exit 1
    ;;
esac

