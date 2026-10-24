#!/bin/zsh
set -eu
ROOT=${0:A:h:h}
exec "$ROOT/harness2/.venv/bin/python" "$ROOT/scripts/open_local.py" bonsai "$@"
