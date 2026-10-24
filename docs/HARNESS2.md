# Harness² compatibility evidence

Upstream: https://github.com/google-research/harness2 at 1cfe254e8d25b15f37048c3730134686abe60335. Setup: https://github.com/google-research/harness2/blob/main/docs/SETUP.md. Installed editable core without render/bridge extras in a Python3.12.13 environment. No upstream file edited.

Executed officially, unmodified:

```sh
uv venv --python 3.12 harness2/.venv
uv pip install --python harness2/.venv/bin/python -e harness2/upstream
harness2/.venv/bin/harness2-demo --output harness2/runs/demo-k1 --k 1 --mode sequential
```

Exit0. Demo report: 2 completed, 0 failed, execution_count8, editor_calls8. Uses deterministic editors and real Python executions, no LLM. A portable copy of demo.json is kept in benchmarks/results. Repeat with scripts/run_harness_demo.sh.

Exact constraints found in the inspected source:

| Area | Source | Finding |
|---|---|---|
| Documented benchmark platform | docs/SETUP.md:9–23 | Linux/Python3.12; apt dependencies; WorkBuddy requires Docker Engine |
| Native demo | harness2/cli/demo.py:35–50 | DemoAdapter + DemoProposer + core.schedule.run_domain; sequential supported |
| OpenCode pin | harness2/config.py:104–114,130–131 | Dedicated dependencies/opencode and dependencies/tools/.../bun |
| Solver launcher | harness2/substrate/opencode.py:226–259 | bun run --cwd packages/opencode --conditions=browser src/index.ts |
| Improver launcher | harness2/core/proposer.py:253–302,396–403 | Separate source checkout; MISSION.md and output/answer.md; environment configurable |
| Models | harness2/config.py:99–102 | HARNESS2_SOLVER_MODEL, HARNESS2_IMPROVER_MODEL, HARNESS2_JUDGE_MODEL |
| Default cloud setup | docs/SETUP.md:28–66 | Vertex credentials; do not execute these steps |
| Alternative judge endpoint | harness2/config.py:152–153 | HARNESS2_JUDGE_BASE_URL/API_KEY exists; not proof that every benchmark is local-compatible |

The core itself is not inherently Linux-only: its deterministic demo passed on macOS. Do not describe absent Bun/source dependencies as mandatory Linux incompatibility. WorkBuddy cannot run under the user's no-container rule. LAB/JobBench and official model-backed optimization have not been validated natively or with Ornith. A local F7 Propose-Probe-Compose reproduction may reuse protocol ideas while using the installed OpenCode; it must never be reported as the official benchmark runner.
