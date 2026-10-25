# Measured results

Generated 2026-10-25T15:09:24.308598+00:00 from versioned JSON evidence.

**Exploratory comparison.** Short benchmarks have three repetitions; each F7/configuration is a single run. These are new public equivalents, not historical F7. No conclusive superiority claim from one task run.

| Indicator | Bonsai GGUF | Ornith MLX | Ornith GGUF | Ornith + local PPC |
|---|---|---|---|---|
| Decode t/s | 4.65 (4.24–5.61, n=3) | 15.43 (14.73–15.50, n=3) | 10.06 (9.71–10.07, n=3) | same runtime; no separate micro |
| Prefill t/s | 22.05 (19.31–22.37, n=3) | 83.02 (64.58–86.29, n=3) | 75.52 (71.07–89.59, n=3) | same runtime; no separate micro |
| Peak measured server RSS | 7.27 GiB peak RSS | 3.79 GiB peak RSS | 6.37 GiB peak RSS | 4.35 GiB peak RSS |
| Tool cycles | read cycle verified | 3/3 | 3/3 | see F7 tool events |
| F7 artifact acceptance | 4/4 | 3/4 | 3/4 | 2/4 |
| F7 agent completions | 4/4 scored | 2/4 scored | 3/4 scored | 2/4 scored |
| Agent wall/task | 578.0 s median, 4 completed tasks | 996.6 s median, 2 completed tasks | 518.1 s median, 3 completed tasks | 541.6 s median, 2 completed tasks |
| System swap during tasks | 0.93–0.94 GiB system swap | 0.72–0.83 GiB system swap | 0.49–6.52 GiB system swap | 0.49–1.53 GiB system swap |

Rates use native runtime counters: llama.cpp HTTP timing fields and MLX direct stream_generate counters. These differ from HTTP latency. Ornith affine4 MLX and Q4_K_M GGUF also differ in quantization, so their quality difference cannot be attributed solely to runtime. Bonsai versus Ornith is a model-plus-runtime comparison. Missing measurements remain N/E.

MLX HTTP transport measurements: TTFT 0.60 s (0.59–10.61, n=3); wall 7.99 s (7.97–15.97, n=3). True prefill rate is not estimated from TTFT.

The cleared-host cohort is kept separate from the earlier memory-congested block. Once its first row exists, this report uses only that cohort for each condition; it never fills missing rows from the older block. Old negative outcomes remain in the raw evidence.

## Artifact acceptance versus agent completion

- Bonsai control: 4/4 artifacts pass external tests; agent completions: 4/4 scored.
- Ornith MLX control: 3/4 artifacts pass external tests; agent completions: 2/4 scored.
- Ornith GGUF control: 3/4 artifacts pass external tests; agent completions: 3/4 scored.
- Ornith local PPC: 2/4 artifacts pass external tests; agent completions: 2/4 scored.

The earlier congested-block Ornith F7-B artifact passes all three tests, but its agent timed out at1200 seconds. This illustrates why artifact correctness and completed-agent productivity are separate.

## External acceptance by task

| Configuration | Task | Outcome | Agent seconds | Tool calls | Tool errors | Tests immutable |
|---|---|---|---|---|---|---|
| Bonsai control | F7-A | pass | 534.48 | 10 | 0 | True |
| Bonsai control | F7-B | pass | 401.34 | 6 | 0 | True |
| Bonsai control | F7-C | pass | 621.60 | 9 | 0 | True |
| Bonsai control | F7-D | pass | 628.68 | 12 | 0 | True |
| Ornith MLX control | F7-A | fail | 507.40 | 7 | 0 | True |
| Ornith MLX control | F7-B | fail | 1200.04 | 12 | 0 | True |
| Ornith MLX control | F7-C | pass | 826.88 | 9 | 0 | True |
| Ornith MLX control | F7-D | pass | 1166.25 | 14 | 0 | True |
| Ornith GGUF control | F7-A | fail | 749.89 | 15 | 0 | True |
| Ornith GGUF control | F7-B | pass | 404.94 | 10 | 0 | True |
| Ornith GGUF control | F7-C | pass | 565.48 | 9 | 0 | True |
| Ornith GGUF control | F7-D | pass | 518.12 | 14 | 0 | True |
| Ornith local PPC | F7-A | fail | 559.81 | 7 | 0 | True |
| Ornith local PPC | F7-B | pass | 596.62 | 12 | 0 | True |
| Ornith local PPC | F7-C | fail | 1200.05 | 10 | 0 | True |
| Ornith local PPC | F7-D | pass | 486.61 | 12 | 0 | True |

Failed acceptance, timeouts and infrastructure errors are retained. Passing artifact tests after an agent timeout is reported separately in raw JSON; it is not an end-to-end successful run. Tool errors count error events; they are not automatically equivalent to model retries. Context compaction and auxiliary requests are represented by raw event traces and server logs.

First-tool latency in observability.json is derived from the earliest tool state.time.start, including parallel calls. Older raw task summaries captured completion-event time; their saved traces are preserved and recomputed here. Missing start timestamps remain unmeasured.

## Bonsai to Ornith MLX — paired passing tasks

- F7-C: -33.0% agent-wall reduction (621.6 → 826.9 s), one run per condition.
- F7-D: -85.5% agent-wall reduction (628.7 → 1166.3 s), one run per condition.

## Ornith MLX to GGUF — paired passing tasks

- F7-C: 31.6% agent-wall reduction (826.9 → 565.5 s), one run per condition.
- F7-D: 55.6% agent-wall reduction (1166.3 → 518.1 s), one run per condition.

## Harness effect — paired passing tasks

- F7-D: 58.3% agent-wall reduction (1166.3 → 486.6 s), one run per condition.

## Harness cost and provenance

Official unmodified Harness² deterministic demo: k1 sequential, 2/2 tasks, 8 Python executions, 8 deterministic editor calls. It does not measure Ornith. Official model-backed benchmark suites were not executed. WorkBuddy requires Docker and is excluded. The pinned source-executor validation and official core with local F7/macOS adapters are tracked separately in docs/HARNESS2.md and harness-official-local-*.json; the local PPC results below must not be attributed to that core.

Local Propose–Probe–Compose reproduction: k1, sequential, one worker, same Ornith MLX solver/improver/composer, DEV only. Optimization wall: 1562.8721079580027 seconds. That cost is separate from every final task wall. Composition is frozen before F7 optimized runs; F7 prompts, acceptance scores and solutions were not provided to the editor.

- DEV control: artifact acceptance True; agent status fail; timeout True. Textual composition validity alone is not a demonstrated improvement.
- DEV probe: artifact acceptance True; agent status fail; timeout True. Textual composition validity alone is not a demonstrated improvement.

## Not executed and limits

- Official model-backed Harness² benchmark adapters: not executed. The local reproduction is explicitly distinct.
- Three independent repetitions per long F7 task/configuration, seed blocks, thermal crossover and long-session soak: not executed.
- Production code review and security assessment: not scored by these bounded acceptance tests.
- A causal no-swapping claim is not established from system swap alone; inspect sampled deltas and unrelated activity. The cleared-host block started at903 MiB used swap.
- MLX does not expose a reasoning-token usage split here; reported zero reasoning tokens is not evidence that the model did not reason. Separate reasoning content was verified through the API.

## Recommendation

Prioritize externally correct completed tasks. Preserve Bonsai as the reference. Use measured task outcomes and wall time above; a conclusive overall model/runtime/harness advantage requires the missing controlled repetitions.
