#!/bin/zsh
# D059/D061 control cohort oc232-nodocker with the D051 memory gate running alongside; the gate stops when the campaign exits.
set -u
ROOT=${0:A:h:h}; cd "$ROOT"; PY=benchmarks/.venv/bin/python
$PY scripts/memory_gate.py oc232 & GATE=$!; trap "kill $GATE" EXIT
LAB_LABEL=oc232-nodocker $PY scripts/campaign_models.py "$@"
