#!/usr/bin/env bash
# Thin wrapper so `./install.sh` works from a checkout.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$ROOT/scripts/install.py" "$@"
