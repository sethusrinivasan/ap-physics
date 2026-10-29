#!/usr/bin/env bash
# install_deps.sh - Install all system and Python dependencies for the ap-physics-walkthrough skill
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "======================================================================"
echo "  ap-physics-walkthrough: Dependency Installer & Environment Setup"
echo "======================================================================"

# 1. Detect Operating System
OS="$(uname -s)"
echo "▶ Detecting Operating System: $OS"

install_system_deps() {
  case "$OS" in
    Linux*)
      if command -v apt-get >/dev/null 2>&1; then
        echo "✔ Debian/Ubuntu detected. Installing poppler-utils..."
        if [ "$EUID" -eq 0 ]; then
          apt-get update -y && apt-get install -y poppler-utils
        elif command -v sudo >/dev/null 2>&1; then
          sudo apt-get update -y && sudo apt-get install -y poppler-utils
        else
          echo "⚠ Please run: sudo apt-get install -y poppler-utils"
        fi
      elif command -v dnf >/dev/null 2>&1; then
        echo "✔ Fedora/RHEL detected. Installing poppler-utils..."
        if [ "$EUID" -eq 0 ]; then
          dnf install -y poppler-utils
        elif command -v sudo >/dev/null 2>&1; then
          sudo dnf install -y poppler-utils
        else
          echo "⚠ Please run: sudo dnf install -y poppler-utils"
        fi
      elif command -v pacman >/dev/null 2>&1; then
        echo "✔ Arch Linux detected. Installing poppler..."
        if [ "$EUID" -eq 0 ]; then
          pacman -S --noconfirm poppler
        elif command -v sudo >/dev/null 2>&1; then
          sudo pacman -S --noconfirm poppler
        else
          echo "⚠ Please run: sudo pacman -S --noconfirm poppler"
        fi
      elif command -v apk >/dev/null 2>&1; then
        echo "✔ Alpine Linux detected. Installing poppler-utils..."
        apk add --no-cache poppler-utils
      else
        echo "⚠ Unknown Linux distribution. Ensure 'pdftoppm' and 'pdftotext' are installed."
      fi
      ;;
    Darwin*)
      echo "✔ macOS detected."
      if command -v brew >/dev/null 2>&1; then
        echo "Installing poppler via Homebrew..."
        brew install poppler
      else
        echo "⚠ Homebrew not found. Please install poppler manually: brew install poppler"
      fi
      ;;
    *)
      echo "⚠ Unsupported OS: $OS. Please install Poppler tools (pdftoppm, pdftotext) manually."
      ;;
  esac
}

# 2. Check and install Poppler system tools if missing
if ! command -v pdftoppm >/dev/null 2>&1 || ! command -v pdftotext >/dev/null 2>&1; then
  echo "▶ System tools (pdftoppm, pdftotext) missing. Installing..."
  install_system_deps
else
  echo "✔ System tools (pdftoppm, pdftotext) already present."
fi

# 3. Check and install Python dependencies
echo "▶ Checking Python environment..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Error: python3 is not installed. Please install Python 3.10+." >&2
  exit 1
fi

PIP_FLAGS=()
if python3 -c 'import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)' 2>/dev/null; then
  echo "✔ Active virtual environment detected."
else
  PIP_FLAGS+=(--user --break-system-packages)
fi

echo "▶ Installing Python packages from requirements.txt..."
python3 -m pip install "${PIP_FLAGS[@]}" -r "$REPO_ROOT/requirements.txt"

# 4. Optional: Install browser for full Playwright E2E tests
if [ "${INSTALL_BROWSER:-}" = "true" ] || [[ "${*:-}" == *"--with-browser"* ]]; then
  echo "▶ Installing Playwright Chromium browser..."
  python3 -m playwright install chromium || true
fi

# 4. Verify installation
echo "▶ Verifying installed components..."
ERRORS=0

if command -v pdftoppm >/dev/null 2>&1; then
  echo "  ✔ pdftoppm: $(pdftoppm -v 2>&1 | head -n 1)"
else
  echo "  ❌ pdftoppm is missing"
  ERRORS=$((ERRORS + 1))
fi

if command -v pdftotext >/dev/null 2>&1; then
  echo "  ✔ pdftotext: $(pdftotext -v 2>&1 | head -n 1)"
else
  echo "  ❌ pdftotext is missing"
  ERRORS=$((ERRORS + 1))
fi

python3 -c "
import PIL
import qrcode
import importlib.metadata
try:
    qr_ver = importlib.metadata.version('qrcode')
except Exception:
    qr_ver = getattr(qrcode, '__version__', 'unknown')
print('  ✔ Pillow (PIL):', PIL.__version__)
print('  ✔ qrcode:', qr_ver)
" || {
  echo "  ❌ Failed to load Python packages (PIL or qrcode)"
  ERRORS=$((ERRORS + 1))
}

echo "======================================================================"
if [ "$ERRORS" -eq 0 ]; then
  echo "  🎉 SUCCESS: All dependencies installed and ready!"
  echo "  You can now run:"
  echo "    python3 skills/ap-physics-walkthrough/scripts/run_unit_pipeline.py \\"
  echo "      --unit <N> --title \"<Title>\" --questions <q.pdf> --answers <a.pdf>"
  echo "======================================================================"
  exit 0
else
  echo "  ❌ SETUP INCOMPLETE: $ERRORS check(s) failed."
  echo "======================================================================"
  exit 1
fi
