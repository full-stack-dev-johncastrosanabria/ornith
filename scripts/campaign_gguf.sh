#!/bin/zsh
# Sequential follow-on: wait for the selected owned campaign, then validate GGUF.
set -eu
ROOT=${0:A:h:h}
cd "$ROOT"
PY="$ROOT/harness2/.venv/bin/python"
if [[ $# != 1 || "$1" != <-> ]]; then
  echo 'Usage: zsh scripts/campaign_gguf.sh CAMPAIGN_PID'
  exit 2
fi
CAMPAIGN_PID=$1
while /bin/ps -p "$CAMPAIGN_PID" -o command= | /usr/bin/grep -Fq "$ROOT/scripts/campaign.py"; do
  sleep 10
done
# Do not continue a resource-blocked/interrupted campaign or overlap a model.
"$PY" - "$CAMPAIGN_PID" <<'PY'
import json,pathlib,sys
sys.path.insert(0,'scripts')
from server import active,STATE
from memory import require_space
records=[json.loads(p.read_text()) for p in pathlib.Path('logs').glob('campaign-20*.json')]
record=next(d for d in records if d['pid']==int(sys.argv[1]))
assert record['status'] in ['stages_finished','stages_finished_with_errors'], record['status']
assert not pathlib.Path('logs/campaign.lock').exists(), 'Another campaign owns the lab'
assert not STATE.exists(), 'Inference server state still present; inspect before proceeding'
active();require_space()
PY
zsh scripts/setup_gguf.sh
"$PY" scripts/server.py start gguf
trap '"$PY" scripts/server.py stop' EXIT
"$PY" scripts/smoke_api.py
"$PY" scripts/smoke_agent.py
"$PY" scripts/bench_api.py --label cleared-host
"$PY" scripts/bench_tasks.py --label control-cleared-host
"$PY" scripts/server.py stop
trap - EXIT
"$PY" scripts/report.py
echo 'GGUF sequence finished; inspect results before drawing conclusions.'
