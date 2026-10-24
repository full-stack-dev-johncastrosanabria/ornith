#!/bin/zsh
set -eu
ROOT=${0:A:h:h}
cd "$ROOT"
REV=1cfe254e8d25b15f37048c3730134686abe60335
if [[ ! -d harness2/upstream/.git ]]; then
  git clone --no-checkout https://github.com/google-research/harness2.git harness2/upstream
  git -C harness2/upstream checkout --detach "$REV"
fi
[[ $(git -C harness2/upstream rev-parse HEAD) == "$REV" ]] || { echo 'Unexpected upstream SHA; inspect before proceeding.'; exit 1; }
[[ -z $(git -C harness2/upstream status --porcelain) ]] || { echo 'Upstream is dirty; preserve and inspect changes.'; exit 1; }
[[ -d harness2/.venv ]] || uv venv --python 3.12 harness2/.venv
uv pip install --python harness2/.venv/bin/python harness2/upstream
git -C harness2/upstream clean -fd -- build harness2.egg-info
