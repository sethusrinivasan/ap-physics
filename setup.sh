#!/usr/bin/env bash
# setup.sh - Convenience wrapper to install all dependencies for ap-physics-walkthrough
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/skills/ap-physics-walkthrough/scripts/install_deps.sh" "$@"
