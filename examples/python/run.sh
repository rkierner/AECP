#!/usr/bin/env bash
# Run the Python example agent in an isolated virtual environment.
# Usage: bash run.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_DIR="$SCRIPT_DIR/../../sdk/python"
VENV_DIR="$SCRIPT_DIR/.venv"

# ── Find a suitable Python interpreter ────────────────────────────────────────
# Prefer an explicit 3.x version; macOS system python3 is stuck at 3.9.
find_python() {
  for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" &>/dev/null; then
      version=$("$candidate" -c 'import sys; print(sys.version_info[:2])')
      # Accept 3.9 or newer
      if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' 2>/dev/null; then
        echo "$candidate"
        return
      fi
    fi
  done
  echo ""
}

PYTHON=$(find_python)
if [ -z "$PYTHON" ]; then
  echo "ERROR: No Python 3.9+ interpreter found."
  echo "Install one via Homebrew:  brew install python@3.12"
  exit 1
fi

echo "[setup] Using interpreter: $PYTHON ($($PYTHON --version))"

# ── Create venv if needed ──────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
  echo "[setup] Creating virtual environment..."
  "$PYTHON" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "[setup] Installing SDK and dependencies..."
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e "$SDK_DIR[kafka]"
python -m pip install --quiet -r "$SCRIPT_DIR/requirements.txt"

echo "[run] Starting jira_agent.py..."
echo ""
python "$SCRIPT_DIR/jira_agent.py" "$@"
