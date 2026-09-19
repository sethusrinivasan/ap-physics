#!/usr/bin/env bash
# Install test dependencies (Python venv + Playwright Chromium) and run the suite.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Install Python 3.10+ and retry." >&2
  exit 1
fi

PIP_ARGS=()
PY=""

venv_usable() {
  [ -x .venv/bin/python ] && .venv/bin/python -m pip --version >/dev/null 2>&1
}

if ! venv_usable; then
  rm -rf .venv
  if python3 -m venv .venv >/dev/null 2>&1 && venv_usable; then
    :
  elif python3 -m venv --without-pip .venv >/dev/null 2>&1 && [ -x .venv/bin/python ]; then
    echo "Bootstrapping pip into .venv (python3-venv / ensurepip not available)."
    if command -v curl >/dev/null 2>&1; then
      curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python
    else
      python3 -c "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', '/tmp/get-pip.py')"
      .venv/bin/python /tmp/get-pip.py
    fi
  fi
fi

if venv_usable; then
  PY=".venv/bin/python"
else
  echo "Could not create .venv. Installing packages with: python3 -m pip --user"
  rm -rf .venv
  PY="python3"
  PIP_ARGS=(--user --break-system-packages)
fi

"$PY" -m pip install -U pip "${PIP_ARGS[@]}"
"$PY" -m pip install "${PIP_ARGS[@]}" -r requirements.txt

if [ "${CI:-}" = "true" ]; then
  "$PY" -m playwright install --with-deps chromium
else
  "$PY" -m playwright install chromium
fi

BASE_URL="${BASE_URL:-https://sethusrinivasan.github.io/ap-physics/}"
export BASE_URL
echo "Running tests against ${BASE_URL}"
"$PY" -m unittest discover -s tests -v
