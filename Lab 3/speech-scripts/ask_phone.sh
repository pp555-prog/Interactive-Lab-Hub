#!/usr/bin/env bash
# Ask for a numerical answer, record it, and show Whisper's uncorrected transcript.
set -euo pipefail
LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$LAB_DIR/.venv/bin/python"
VOICE="$LAB_DIR/voices/en_US-lessac-medium.onnx"
MIC="${LAB3_MIC_DEVICE:-plughw:CARD=w1080p,DEV=0}"
if [[ ! -x "$PYTHON" || ! -f "$VOICE" || ! -f "$VOICE.json" ]]; then
  echo "Complete the Lab 3 virtual environment and speech setup first." >&2
  exit 1
fi
mkdir -p "$LAB_DIR/recordings"
PROMPT="$(mktemp /tmp/lab3-phone-prompt-XXXXXX.wav)"
trap 'rm -f -- "$PROMPT"' EXIT
"$PYTHON" -m piper --model "$VOICE" --output-file "$PROMPT" -- \
  "What is your phone number?"
pw-play "$PROMPT"
ANSWER="$(mktemp "$LAB_DIR/recordings/phone-$(date +%Y%m%d-%H%M%S)-XXXXXX.wav")"
echo "Speak now. Recording for ten seconds..."
arecord -D "$MIC" -f S16_LE -r 16000 -c 1 -d 10 "$ANSWER"
echo "Saved answer: $ANSWER"
"$PYTHON" "$LAB_DIR/speech-scripts/transcribe.py" "$ANSWER" --model tiny.en
