#!/bin/zsh
# D061 (g, e): per model, agent smoke + DEV once under the oc232 protocol; Bonsai-2-9B also reruns the excluded F8-A pilot with reserved = output cap.
set -u
ROOT=${0:A:h:h}; cd "$ROOT"; PY=benchmarks/.venv/bin/python
export LAB_AGENT_STEPS=40
$PY scripts/memory_gate.py devfilter & GATE=$!; trap "kill $GATE" EXIT
for k in "$@"; do
  $PY scripts/server.py start $k || { echo "$k: start failed (infrastructure)"; continue; }
  if $PY scripts/smoke_agent.py; then
    $PY scripts/bench_tasks.py --tasks DEV --label oc232-devfilter --timeout 1800
    [[ $k == bonsai9 ]] && $PY scripts/bench_tasks.py --tasks F8-A --label oc232-pilot-reserve --timeout 1800
  else echo "$k: smoke gate failed (integration N/E)"; fi
  $PY scripts/server.py stop
done
$PY scripts/score_models.py --label oc232-devfilter --kinds "$@" --dev-filter
