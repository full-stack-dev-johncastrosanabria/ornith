# Harness² compatibility evidence

Upstream: https://github.com/google-research/harness2 at 1cfe254e8d25b15f37048c3730134686abe60335. Setup: https://github.com/google-research/harness2/blob/main/docs/SETUP.md. Installed editable core without render/bridge extras in a Python3.12.13 environment. No upstream file edited.

Executed officially, unmodified:

```sh
uv venv --python 3.12 harness2/.venv
uv pip install --python harness2/.venv/bin/python -e harness2/upstream
harness2/.venv/bin/harness2-demo --output harness2/runs/demo-k1 --k 1 --mode sequential
```

Exit0. Demo report: 2 completed, 0 failed, execution_count8, editor_calls8. Uses deterministic editors and real Python executions, no LLM. A portable copy of demo.json is kept in benchmarks/results. Repeat with scripts/run_harness_demo.sh. After the initial editable install, switched to a non-editable local wheel and removed only generated build/egg-info/bytecode directories, so upstream stays a clean source reference. No tracked source was changed.

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

## Bounded local harness experiment

The official CLI supports JB/LAB/WB, not these F7 fixtures. Custom local providers are plausible through OpenCode configuration; a mandatory remote-model requirement for the entire optimizer has **not** been established. We do not claim that the core is incompatible with local inference. A true upstream F7 integration would need a benchmark adapter plus the pinned Bun/OpenCode source runner and its configuration. This lab instead implements the explicitly labeled minimal methodology reproduction allowed by the mission, reusing its own fixture/evaluation/OpenCode components.

| Component | Investigated extension | Local scope |
|---|---|---|
| System prompt | Upstream always-on harness files and proposer/composer | One model-generated guidance candidate, DEV probe, frozen composition |
| Tool guidance | tool_descriptions/tool_guidance.md; compose_prompt staging | Guidance paragraph only; tool implementations unchanged |
| Skills | skills/*/SKILL.md advertised by upstream compose_prompt | Not activated in this initial single-worker experiment |
| Memory | Core library and harnessing-level retained lessons | Only the frozen guidance file persists; no claim of upstream experience reflection |
| Scripts | Upstream script staging and native Python/Bash hooks | Shared local test/measurement scripts; not optimized by this k1 run |
| Execution | Sequential recursion and installed OpenCode | k1, one worker, no delegation or parallel recursion |
| Compaction | Native OpenCode automatic compaction | Infrastructure feature, not an independently optimized treatment |

Differences from the official algorithm: one candidate rather than general/domain candidate branching, no official benchmark adapter, no upstream source executor, no recursive experience-reflector/library update, no remote or model judge. Public external acceptance is recorded independently; proposal/composition receive only DEV execution observations, never F7 prompts/acceptance scores/solutions. The final control and treatment share the same model, runtime, sampling, context, output cap, tool permissions and tests. Optimization wall/calls/tokens are separate from final-task costs.

## Official-core integration, authorized extension

The user approved adding an official-core phase. `scripts/harness_official.py` invokes upstream `run_domain`, recursion, proposal/composition, selection, reflection and library code. This is **official Harness² core with local macOS/F7 adapters**, not the stock benchmark CLI or an upstream-supported F7 benchmark. It remains unvalidated with real model calls until its own execution evidence exists.

`scripts/setup_harness_official.py` installs only the pinned source executor: OpenCode `23fb5e0516c99ac04a1aa46c193efda2e1b9bb24`, the upstream compatibility patch, and Bun1.3.11. These live under `harness2/official/dependencies/`; the clean Harness² reference and global OpenCode stay unchanged. Its downloader/installer checks the8GiB reserve during each child process and stops the owned process group if needed. No official Linux benchmark, Docker, Vertex credentials or cloud judge is installed.

The adapters provide:

- Local Ornith MLX for solver, proposer and reflector through one endpoint, with isolated configuration, stripped credentials, localhost-only networking, workspace confinement and protected acceptance tests.
- The official pinned source launcher under native Seatbelt. Baseline and treatment both use this executor, independently from the global-OpenCode cohort.
- DEV-only optimization and reflection. Held-out F7 tasks are executed only after freezing a validated changed text harness; their acceptance results never enter the optimizer.
- Always-on text editing only in this first official-core run. Skills, scripts, plugins and delegated agents are rejected by adapter validation rather than silently ignored.
- `k=1`, sequential recursion, one proposer worker and one rollout worker. Upstream sequential defaults to two proposer workers; a local dispatch wrapper supplies its existing worker arguments without editing upstream code.
- Independent acceptance from the existing public F7 tests, with optimization wall time reported separately.

Six no-model checks in `scripts/test_harness_official.py` pass, including a real upstream-core cycle over the local adapter with a deterministic test editor, infrastructure-safe resume and editor token/session audit. This verifies adapter plumbing, not Ornith performance or the pinned source executor. The real run first requires3/3 source-executor smoke cycles, then a fresh F7 source-executor control, DEV optimization, and held-out treatment. A failed setup/parser or absent changed composition is recorded as incomplete; no benefit is invented. Infrastructure interruptions halt a condition; resuming archives that raw attempt and retries only unscored work, preserving measured pass/fail outcomes through the shared campaign completion policy. The optimization result records separate editor/DEV solver session metrics from native event traces; provider retries and auxiliary usage not exposed by the CLI remain unmeasured.

The native follow-on controller `scripts/campaign_official.py --after-pid GGUF_CONTROLLER_PID` waits for the queued GGUF phase, checks absence of another server, locks the laboratory and runs setup/preflight/API/official-core stages with separate logs. Resource or integration failures leave raw evidence and stop the affected phase. See `logs/official-campaign-*.json`, `logs/official-*.log`, `benchmarks/results/harness-official-local-*.json`, and `benchmarks/reports/harness-official-comparison.json` when produced.

The first real source smoke stopped before inference with Bun's `CouldntReadCurrentDirectory`. The local launch boundary now permits directory reads on literal checkout ancestors, including the home directory itself; child files and subdirectories remain denied unless separately allowed. No source-checkout write permission was added. Native pinned-source startup and isolated config validation pass, and private-file/outside-write probes remain denied (`benchmarks/results/official-source-launch-check.json`). After this correction,3/3 real model-backed source cycles passed in59.8/130.3/186.1 s (`benchmarks/results/smoke-agent-mlx-20261025T090125.json`). This establishes source-executor integration, not an optimization benefit. The controller then starts its separate F7 source control, DEV optimization and held-out treatment.
