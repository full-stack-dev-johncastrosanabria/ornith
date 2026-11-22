#!/bin/zsh
# D063: Ornith decode speed at 16K vs 24K context (ABA: 16K, 24K, 16K), idle Mac, bench_api micro (3 x 512 tokens), own gate log.
ROOT=${0:A:h:h}; cd "$ROOT"; PY=benchmarks/.venv/bin/python
$PY scripts/memory_gate.py oc232-ctxspeed & GATE=$!; trap "kill $GATE; $PY scripts/server.py stop" EXIT
for arm in 16k:runtimes/profile.json 24k:runtimes/profile-daily.json 16k:runtimes/profile.json; do
  export LAB_PROFILE=${arm#*:}
  echo "arm ${arm%%:*} wired-before $(vm_stat | awk -F: '/wired/{gsub(/[ .]/,"",$2);printf "%.2f GB",$2*16384/1073741824}')"
  $PY scripts/server.py start gguf || continue
  echo "arm ${arm%%:*} wired-loaded $(vm_stat | awk -F: '/wired/{gsub(/[ .]/,"",$2);printf "%.2f GB",$2*16384/1073741824}')"
  $PY scripts/bench_api.py --repeats 3 --max-tokens 512 --label d063-${arm%%:*}
  $PY scripts/server.py stop
  sleep 120
done
