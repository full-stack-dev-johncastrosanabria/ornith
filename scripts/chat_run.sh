#!/bin/zsh
# D062: chat-mode check (descriptive): 8 single-turn prompts x 3 per kind, daily profile (24K/4096), own memory-gate log;
# grading runs only after the last server is stopped.
ROOT=${0:A:h:h}; cd "$ROOT"; PY=benchmarks/.venv/bin/python
export LAB_PROFILE=runtimes/profile-daily.json
$PY scripts/memory_gate.py oc232-chat & GATE=$!; trap "kill $GATE; $PY scripts/server.py stop" EXIT
for kind in "$@"; do
  sleep 300  # same idle cooldown as the cohort before every model
  $PY scripts/server.py start $kind || continue
  $PY scripts/bench_chat.py
  $PY scripts/server.py stop
done
$PY scripts/grade_chat.py "$@"
