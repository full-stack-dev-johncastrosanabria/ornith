#!/bin/zsh
# D061 (p): .NET repeat (descriptive only): F7-A and F8-G twice per kind (labels oc232-dotnet-a/-b), cohort profile, 40 steps / 1800 s.
ROOT=${0:A:h:h}; cd "$ROOT"; PY=benchmarks/.venv/bin/python
export LAB_AGENT_STEPS=40
$PY scripts/memory_gate.py oc232-dotnet & GATE=$!; trap "kill $GATE; $PY scripts/server.py stop" EXIT
for kind in "$@"; do
  sleep 300  # same idle cooldown as the cohort before every model
  $PY scripts/server.py start $kind || continue
  if $PY scripts/smoke_agent.py; then
    for rep in a b; do $PY scripts/bench_tasks.py --tasks F7-A F8-G --label oc232-dotnet-$rep --timeout 1800; done
  else echo "$kind smoke gate failed (integration N/E)"; fi
  $PY scripts/server.py stop
done
