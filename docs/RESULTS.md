# Measured results

Generated 2026-10-24T20:51:46.671562+00:00 from versioned JSON evidence.

**Exploratory comparison.** Short benchmarks have three repetitions; each F7/configuration is a single run. These are new public equivalents, not historical F7. No conclusive superiority claim from one task run.

| Indicator | Bonsai GGUF | Ornith MLX | Ornith GGUF | Ornith + local PPC |
|---|---|---|---|---|
| Decode t/s | 6.83 (6.81–6.84, n=3) | N/E | N/E | same runtime; no separate micro |
| Prefill t/s | 24.62 (23.13–24.84, n=3) | N/E | N/E | same runtime; no separate micro |
| Peak measured server RSS | N/E | 1.20 GiB peak RSS | N/E | N/E |
| Tool cycles | read cycle verified | 3/3 | N/E | see F7 tool events |
| F7 tasks | N/E | 0/2 scored | N/E | N/E |
| Agent wall/task | N/E | N/E | N/E | N/E |
| System swap during tasks | N/E | 1.10–7.17 GiB system swap | N/E | N/E |

Rates in the first two rows use native runtime counters: Bonsai HTTP timing fields, MLX direct stream_generate counters (different measurement paths, both fresh KV; not equivalent HTTP latency). For a runtime-only comparison use Ornith GGUF vs Ornith MLX with the same weights family/quantization quality; that comparison remains unexecuted. Do not infer pure runtime effects from Bonsai vs Ornith.

MLX HTTP transport measurements: TTFT 0.77 s (0.74–1.09, n=3); wall 8.90 s (8.76–9.22, n=3). True prefill rate is not estimated from TTFT.

## Artifact acceptance versus agent completion

- Ornith control: 1/2 artifacts pass external tests; 0/2 agent runs completed successfully.

For example, the recorded Ornith F7-B artifact passes all three tests, but its agent run timed out at1200 seconds. This is a productivity/completion failure, not a claim that its final code fails those tests.

## External acceptance by task

| Configuration | Task | Outcome | Agent seconds | Tool calls | Tool errors | Tests immutable |
|---|---|---|---|---|---|---|
| Ornith control | F7-A | fail | 712.50 | 7 | 0 | True |
| Ornith control | F7-B | fail | 1200.07 | 8 | 0 | True |

Failed acceptance, timeouts and infrastructure errors are retained. Passing artifact tests after an agent timeout is reported separately in raw JSON; it is not an end-to-end successful run. Tool errors count error events; they are not automatically equivalent to model retries. Context compaction and auxiliary requests are represented by raw event traces and server logs.

## Harness cost and provenance

Official unmodified Harness² deterministic demo: k1 sequential, 2/2 tasks, 8 Python executions, 8 deterministic editor calls. It does not measure Ornith. Official model-backed benchmark suites were not executed. WorkBuddy requires Docker and is excluded; local model-backed upstream source/Bun integration remains unvalidated.

## Not executed and limits

- Ornith GGUF Q4_K_M: download would leave less than 8 GiB free; neither runtime build nor inference performed. Candidate startup/config files are not validation.
- Official model-backed Harness² benchmark adapters: not executed. The local reproduction is explicitly distinct.
- Three independent repetitions per long F7 task/configuration, seed blocks, thermal crossover and long-session soak: not executed.
- Production code review and security assessment: not scored by these bounded acceptance tests.
- A causal no-swapping claim: not established from system swap alone; inspect sampled swapin/swapout deltas and unrelated system activity. Initial system swap was already 1.23 GiB.

## Recommendation

Prioritize externally correct completed tasks. Preserve Bonsai as the reference. Ornith MLX is usable only to the extent shown by measured tool and task outcomes above; no GGUF preference or conclusive overall model/harness advantage is established without the missing controlled repetitions.
