# Best model and configuration for this hardware

Hardware under test: **MacBook Air M3, 16 GB unified memory, macOS 27.3, 228 GB SSD**, native Apple Silicon only (no container/VM/cloud inference).

This is an **evidence-grounded synthesis**, not a new measurement. Every number below is from the versioned JSON in `benchmarks/results/` as summarized in [RESULTS.md](RESULTS.md); the reading discipline of that report carries over — one long run per F7 task/condition is **exploratory**, decode t/s is **not** agent productivity, and Bonsai-vs-Ornith confounds model, runtime and quantization. See [STATUS.md](STATUS.md) for current blockers.

## Candidate cohort `oc226-nodocker` (2026-11-08/09) — final for this cohort (D049)

Global OpenCode 2.2.6 executor, fixed profile (16K context, 4096 output incl. reasoning, temp 0.6, top_p 0.95, 12 steps, 1200 s per F7 task), Docker closed, 300 s cooldown per model; ranking rule D031 (passes first, then total F7 agent time, then decode). Source: `benchmarks/reports/model-selection-oc226-nodocker.json`, decisions D045–D049.

| # | Model | F7 pass | Total F7 s | Decode t/s | Peak footprint* | Fail causes |
|---|---|---|---|---|---|---|
| 1 | Ornith 1.5 9B GGUF Q4_K_M | 4/4 | 1922 | 10.73 | 5.13 GiB | — (F7-D re-run after a disk-reserve infrastructure stop, D046) |
| 2 | Bonsai 2 27B PTQ1_0 | 4/4 | 2113 | 4.52 | 2.40 GiB | — |
| 3 | Ternary-Bonsai-2-9B PTQ1_0 | 3/4 | 718 | 14.99 | 1.59 GiB | F7-A incorrect |
| 4 | Qwen3.5-9B MLX 4-bit | 2/4 | 1636 | 13.35 | 8.05 GiB | F7-A, F7-C incorrect |
| 5 | Ornith 1.5 9B MLX 4-bit | 2/4 | 3850 | 17.07 | 7.93 GiB | F7-A timeout, F7-B incorrect (cap hit); no-thinking arm also 2/4 in 725 s |
| N/E | Granite 4.1 8B, Gemma 4 12B, SERA-8B | N/E | N/E | N/E | N/E | agent smoke gate failed (integration N/E, not zero; D047, D048, D049) |

**D049 repeat (`oc226-nodocker-r2`, 2026-11-09 02:4x–03:5x) and verdict.** Both models repeated the full stages under the same profile and host state (llama.cpp binary hash unchanged after the GGUF re-fetch):

| Model | Cohort 1 | Cohort 2 (r2) | Combined (D049 rule) | Decode t/s (r2) |
|---|---|---|---|---|
| **Ornith 1.5 9B GGUF Q4_K_M** | 4/4, 1922 s | 4/4, 1420 s | **8/8, 3342 s** | 11.15 |
| Bonsai 2 27B PTQ1_0 | 4/4, 2113 s | 4/4, 1919 s | 8/8, 4032 s | 4.94 |

**Winner under the pre-registered rule: Ornith 1.5 9B GGUF Q4_K_M (llama.cpp Metal).** No quality difference is detectable at n = 8 (both 8/8); the order rests on time — GGUF was faster in both cohorts (−17 % summed) and decodes ~2.3× faster. Bonsai 2 27B is an equally correct alternative on these tasks at a lower physical footprint\*. Among MLX builds, Qwen3.5-9B and Ornith MLX reached 2/4. \*Footprint is approximate across runtimes: llama.cpp maps weights from file and clean file-backed pages may be omitted (Bonsai 27B's file is 5.5 GiB).

**Best practices on the 16 passed tasks (descriptive, D031; does not change the winner):** both models changed 1–2 existing files per task with small diffs (4–19 changed lines, no files added), left every acceptance test unchanged, introduced 0 ruff violations (Bonsai r2 F7-B removed one) and 0 `dotnet format` violations on F7-A; no output-cap hits; time headroom 39–82 % of the 1200 s limit. Source: `practices`/`headroom` in `benchmarks/reports/model-selection-oc226-nodocker{,-r2}.json`. The sections below are the earlier cleared-host cohort under a different executor and are kept as history; they are not comparable row-for-row.

## Bottom line (earlier cleared-host cohort, historical — superseded by the section above)

| Use case on this M3 / 16 GB | Pick | Why (measured) |
|---|---|---|
| **Hardest / correctness-critical coding** | **Bonsai 2 27B** (ternary PTQ1_0, llama.cpp Metal) | Only condition passing **4/4** F7 tasks incl. the C# task, tests immutable. Accept slow decode and run on a cleared host. |
| **Best all-round local coder** | **Ornith 1.5 9B GGUF Q4_K_M** (llama.cpp Metal) | **3/4** artifacts **and 3/4** end-to-end completions, decode 10.06 t/s, fastest median completed wall (518 s), RSS 6.37 GiB. |
| **Interactive / lowest latency / lowest memory** | **Ornith 1.5 9B MLX 4-bit** | Fastest decode **15.43 t/s**, prefill 83 t/s, lightest **3.79 GiB** RSS. Weaker on hard tasks (3/4 artifacts, 2/4 completions; one 1200 s timeout) — give it a longer timeout. |

No single configuration dominates on this evidence. Correctness favors the 27B model; speed and footprint favor the 9B MLX build; the 9B GGUF build is the best balance of completions, decode speed and memory.

## Per-model evidence (cleared-host cohort)

| Model / runtime | Decode t/s | Prefill t/s | Peak server RSS | F7 artifacts | F7 completions | Median wall (completed) |
|---|---|---|---|---|---|---|
| Bonsai 2 27B ternary / llama.cpp | 4.65 (4.24–5.61) | 22.05 | 7.27 GiB | **4/4** | **4/4** | 578 s (401–629) |
| Ornith 9B MLX 4-bit / MLX-LM | **15.43** (14.73–15.50) | **83.02** | **3.79 GiB** | 3/4 | 2/4 | 996 s (n=2) |
| Ornith 9B GGUF Q4_K_M / llama.cpp | 10.06 (9.71–10.07) | 75.52 | 6.37 GiB | 3/4 | 3/4 | 518 s (n=3) |

Memory headroom matters on 16 GB: the 27B model's 7.27 GiB resident set fits but is the heaviest, and in earlier memory-congested conditions 27B runs drove system swap high — run it only on a cleared host. The 9B MLX build (3.79 GiB) is the comfortable default; the 9B GGUF build had one task (F7-A) spike system swap to 6.5 GiB, so leave margin.

## Fixed configuration that held across the final matrix

Context **16384**, output cap **4096**, temperature **0.6**, top_p **0.95**, concurrency **1**, KV quantization **none**, **one loaded model at a time** (switch via `scripts/server.py`, stop before switching). Bonsai matches MLX sampling with top-k/min-p filters disabled, `--reasoning-budget 100 --cache-ram 512`. These were frozen after a context-only stability probe (D012/D013); they are the profile all final numbers above were measured under.

## Harness findings

- **Global OpenCode integration** is the validated path for Ornith and backs the 3/4 (MLX) and 3/4 (GGUF) results above.
- **Local Propose–Probe–Compose** reproduction showed **no demonstrated benefit** (2/4 artifacts, 2/4 completions; regressed on F7-C vs. the 3/4 MLX control) and its 1562.9 s optimization cost is separate. Keep it frozen; do not tune on held-out outcomes.
- **Official pinned source-executor** (MLX, same profile) F7 control = **1/4** this cycle; the three failures each truncated at the 4096 output cap (`finish_reason=length`), making the output cap the leading suspected limiter on that path. Its optimization treatment is pending (and currently blocked — see below). Distinct from the global-OpenCode cohort; not pooled.

## Caveats (do not over-read)

- One long run per F7 task/condition. Rankings are exploratory, not conclusive; controlled repetitions, seed blocks, thermal crossover and long-session soak are **not** executed.
- Decode/prefill t/s are native-runtime counters and do **not** by themselves predict agent task productivity.
- Bonsai vs. Ornith mixes model, runtime (llama.cpp vs. MLX) and quantization (ternary vs. 4-bit vs. Q4_K_M); differences cannot be attributed to any one factor.
- Ornith MLX and GGUF cannot be re-run right now — their weights were cleared externally (D027). These findings use the data already on disk.

## What would most strengthen this

1. Re-download the pinned MLX and GGUF revisions (manifests retain them) once ≥8 GiB free is restored, then run ≥3 repetitions per F7 task per model to turn single-run rankings into ranges.
2. Finish the official source-executor DEV optimization + held-out treatment to test whether a guidance change lifts the 1/4 control.
3. A long-session thermal-crossover run to check whether the 9B MLX decode-speed lead holds under sustained load on the Air's passive cooling.
