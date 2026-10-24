# Ornith on native macOS

Local experimental laboratory for Ornith 1.5 9B, MLX-LM, OpenCode, Bonsai 2 27B and Harness² methodology. **Experiment in progress: do not interpret setup/demo success as model superiority.** See [results](docs/RESULTS.md), [protocol](docs/EXPERIMENT.md), [architecture](docs/ARCHITECTURE.md), [baseline](docs/BASELINE.md) and [Harness² compatibility](docs/HARNESS2.md).

## Run locally

From this directory (macOS Apple Silicon only):

```sh
uv venv --python 3.12 runtimes/mlx/.venv
uv pip install --python runtimes/mlx/.venv/bin/python -r runtimes/mlx/requirements.txt
scripts/setup_harness2.sh
uv venv --python 3.12 benchmarks/.venv
uv pip install --python benchmarks/.venv/bin/python -r benchmarks/requirements.txt
runtimes/mlx/.venv/bin/python scripts/download_model.py
scripts/start-ornith-mlx.sh
scripts/opencode-mlx.sh                         # interactive, isolated workspace
harness2/.venv/bin/python scripts/smoke_agent.py # 3 real tool cycles
harness2/.venv/bin/python scripts/bench_api.py   # 3 sequential short HTTP runs
harness2/.venv/bin/python scripts/bench_tasks.py # fresh public F7 copies
harness2/.venv/bin/python scripts/harness_local.py
harness2/.venv/bin/python scripts/bench_tasks.py --label optimized --harness opencode/agents/optimized-guidance.txt
scripts/stop-servers.sh
runtimes/mlx/.venv/bin/python scripts/bench_mlx.py # direct rates; no server active
scripts/run_harness_demo.sh                     # official deterministic demo, no LLM
harness2/.venv/bin/python scripts/memory.py
```

No global OpenCode config is changed. Interactive workspaces must live under `benchmarks/work/`. The launcher isolates all XDG paths, pins primary and auxiliary models to localhost, and enforces native filesystem/network restrictions. Acceptance tests remain read-only. `logs/server.json` records `/v1/models` identifiers and exact argv. Stop waits for the owned server's port to close before permitting a switch. Do not manually run a second model.

## Bonsai and GGUF

```sh
harness2/.venv/bin/python scripts/server.py start bonsai
scripts/opencode-bonsai.sh
harness2/.venv/bin/python scripts/bench_tasks.py
scripts/stop-servers.sh
```

Bonsai reuses the existing PrismML binary/weights read-only; all new logs and work stay here. Its historical fixtures were not located, so the included public F7 fixtures are explicitly new equivalents. Historical 4/4 is not a measured score on this suite.

Ornith Q4_K_M is conditional and currently **not downloaded**: it would violate the 8 GiB free-space margin. `scripts/start-ornith-gguf.sh` refuses to start without independently installed weights/runtime. A candidate config is included, without a claim of runtime validation. Do not use Bonsai's fork for an alleged independent llama.cpp comparison.

`harness2/upstream` is a clean pinned clone, ignored by this parent repository. The official deterministic demo passes natively; official model-backed benchmark adapters remain unvalidated here. `scripts/harness_local.py` is explicitly a local Propose-Probe-Compose reproduction using the installed OpenCode. Its optimization cost is recorded separately; DEV is its only optimization task, final F7 tasks are holdouts.

Raw measured JSON is versioned in `benchmarks/results`; model weights, virtual environments, transient workspaces, OpenCode state and large logs are ignored. This repository has no configured remote.

Current checkpoint: [STATUS.md](docs/STATUS.md). Heavy inference is held for host memory availability; no lab model is left running. Bonsai now uses8085 to preserve the unrelated service on8080. After memory is available, resume missing runs with `harness2/.venv/bin/python scripts/campaign.py --background`; `scripts/test_campaign.py` checks that negative results are retained rather than automatically retried. The campaign uses one native worker and durable stage checkpoints under logs/. Exit75 stops the campaign on the disk reserve guard. The native controller and all evaluated prompts remain distinct from the Ponytail full skill used by Codex.
