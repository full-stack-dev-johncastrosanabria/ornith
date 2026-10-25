# Measured results

Generated 2026-10-25T03:42:29.666349+00:00 from versioned JSON evidence.

**Exploratory comparison.** Short benchmarks have three repetitions; each F7/configuration is a single run. These are new public equivalents, not historical F7. No conclusive superiority claim from one task run.

| Indicator | Bonsai GGUF | Ornith MLX | Ornith GGUF | Ornith + local PPC |
|---|---|---|---|---|
| Decode t/s | 6.83 (6.81–6.84, n=3) | N/E | N/E | same runtime; no separate micro |
| Prefill t/s | 24.62 (23.13–24.84, n=3) | N/E | N/E | same runtime; no separate micro |
| Peak measured server RSS | N/E | 3.79 GiB peak RSS | N/E | 4.35 GiB peak RSS |
| Tool cycles | read cycle verified | 3/3 | N/E | see F7 tool events |
| F7 artifact acceptance | N/E | 3/4 | N/E | 0/1 |
| F7 agent completions | N/E | 2/4 scored | N/E | 0/1 scored; 1 infrastructure |
| Agent wall/task | N/E | 996.6 s median, 2 completed tasks | N/E | N/E |
| System swap during tasks | N/E | 0.72–0.83 GiB system swap | N/E | 1.36–9.05 GiB system swap |

Rates use native runtime counters: llama.cpp HTTP timing fields and MLX direct stream_generate counters. These differ from HTTP latency. Ornith affine4 MLX and Q4_K_M GGUF also differ in quantization, so their quality difference cannot be attributed solely to runtime. Bonsai versus Ornith is a model-plus-runtime comparison. Missing measurements remain N/E.

MLX HTTP transport measurements: TTFT 0.60 s (0.59–10.61, n=3); wall 7.99 s (7.97–15.97, n=3). True prefill rate is not estimated from TTFT.

The cleared-host cohort is kept separate from the earlier memory-congested block. Once its first row exists, this report uses only that cohort for each condition; it never fills missing rows from the older block. Old negative outcomes remain in the raw evidence.

## Artifact acceptance versus agent completion

- Ornith MLX control: 3/4 artifacts pass external tests; agent completions: 2/4 scored.
- Ornith local PPC: 0/1 artifacts pass external tests; agent completions: 0/1 scored; 1 infrastructure.

The earlier congested-block Ornith F7-B artifact passes all three tests, but its agent timed out at1200 seconds. This illustrates why artifact correctness and completed-agent productivity are separate.

## External acceptance by task

| Configuration | Task | Outcome | Agent seconds | Tool calls | Tool errors | Tests immutable |
|---|---|---|---|---|---|---|
| Ornith MLX control | F7-A | fail | 507.40 | 7 | 0 | True |
| Ornith MLX control | F7-B | fail | 1200.04 | 12 | 0 | True |
| Ornith MLX control | F7-C | pass | 826.88 | 9 | 0 | True |
| Ornith MLX control | F7-D | pass | 1166.25 | 14 | 0 | True |
| Ornith local PPC | F7-A | fail | 559.81 | 7 | 0 | True |
| Ornith local PPC | F7-B | infrastructure | 45.60 | N/E | N/E | True |

Failed acceptance, timeouts and infrastructure errors are retained. Passing artifact tests after an agent timeout is reported separately in raw JSON; it is not an end-to-end successful run. Tool errors count error events; they are not automatically equivalent to model retries. Context compaction and auxiliary requests are represented by raw event traces and server logs.

## Harness cost and provenance

Official unmodified Harness² deterministic demo: k1 sequential, 2/2 tasks, 8 Python executions, 8 deterministic editor calls. It does not measure Ornith. Official model-backed benchmark suites were not executed. WorkBuddy requires Docker and is excluded; local model-backed upstream source/Bun integration remains unvalidated.

Local Propose–Probe–Compose reproduction: k1, sequential, one worker, same Ornith MLX solver/improver/composer, DEV only. Optimization wall: 1562.8721079580027 seconds. That cost is separate from every final task wall. Composition is frozen before F7 optimized runs; F7 prompts, acceptance scores and solutions were not provided to the editor.

## Not executed and limits

- Ornith GGUF task matrix is not yet measured. It was initially blocked by disk space; after the user freed resources, a separate pinned native Metal build and Q4_K_M download are scheduled. Candidate configs and build success alone are not validation.
- Official model-backed Harness² benchmark adapters: not executed. The local reproduction is explicitly distinct.
- Three independent repetitions per long F7 task/configuration, seed blocks, thermal crossover and long-session soak: not executed.
- Production code review and security assessment: not scored by these bounded acceptance tests.
- A causal no-swapping claim is not established from system swap alone; inspect sampled deltas and unrelated activity. The cleared-host block started at903 MiB used swap.
- MLX does not expose a reasoning-token usage split here; reported zero reasoning tokens is not evidence that the model did not reason. Separate reasoning content was verified through the API.

## Recommendation

Prioritize externally correct completed tasks. Preserve Bonsai as the reference. Use measured task outcomes and wall time above; a conclusive overall model/runtime/harness advantage requires the missing controlled repetitions.
