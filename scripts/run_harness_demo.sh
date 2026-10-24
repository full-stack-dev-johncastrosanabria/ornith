#!/bin/zsh
set -eu
ROOT=${0:A:h:h}
cd "$ROOT"
exec harness2/.venv/bin/harness2-demo --output "harness2/runs/demo-$(date +%Y%m%dT%H%M%S)" --k 1 --mode sequential
