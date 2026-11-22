#!/bin/zsh
# D061 (o): 24K long-context check (descriptive only): F8-A and F8-C once per kind, 40 steps / 1800 s, own memory-gate log.
ROOT=${0:A:h:h}; cd "$ROOT"; PY=benchmarks/.venv/bin/python
export LAB_AGENT_STEPS=40 LAB_PROFILE=runtimes/profile-24k.json
$PY scripts/memory_gate.py oc232-ctx24k & GATE=$!; trap "kill $GATE; $PY scripts/server.py stop" EXIT
for kind in "$@"; do
  $PY scripts/server.py start $kind || continue
  if $PY scripts/smoke_agent.py; then $PY scripts/bench_tasks.py --tasks F8-A F8-C --label oc232-ctx24k --timeout 1800
  else echo "$kind smoke gate failed at 24K (integration N/E)"; fi
  $PY scripts/server.py stop
done
