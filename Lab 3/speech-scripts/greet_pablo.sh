#!/usr/bin/env bash
# Personalized greeting using Pablo's preferred voice, Piper.
set -euo pipefail
LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$LAB_DIR/.venv/bin/python"
VOICE="$LAB_DIR/voices/en_US-lessac-medium.onnx"
if [[ ! -x "$PYTHON" || ! -f "$VOICE" || ! -f "$VOICE.json" ]]; then
  echo "Complete the Lab 3 virtual environment and speech-scripts/setup.sh first." >&2
  exit 1
fi
AUDIO="$(mktemp /tmp/lab3-greeting-XXXXXX.wav)"
trap 'rm -f -- "$AUDIO"' EXIT
"$PYTHON" -m piper --model "$VOICE" --output-file "$AUDIO" -- \
  "Hello, Pablo. Welcome back. What would you like to work on today?"
pw-play "$AUDIO"
