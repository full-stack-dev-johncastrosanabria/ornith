# Checkpoint — 2026-11-08, resumed; MLX/GGUF weights externally cleared

The experiment remains **incomplete**. The main runtime/harness matrix (16/16 valid task outcomes) and the micro-rate repetitions stand as measured on 2026-10-25 and are unchanged; see [RESULTS.md](RESULTS.md), [DECISIONS.md](DECISIONS.md) (D001–D029) and git history for the full trail. This checkpoint records the resumed-session state only.

## Resume continued (2026-11-08, later) — recovery done, v2.2.6 cohort complete, GitHub synced

- **Disk recovered:** with the user's per-item approval, removed only the stale `default-no-608db` Docker workspace + build cache (novahub evaluation, both DB volumes, and the running `rembric` service kept and verified). Free disk 5.3→15→~22 GiB after the model pull. See D028.
- **Ornith MLX restored + validated:** re-downloaded the pinned revision (size-checked) and confirmed a correct direct HTTP completion. The `models/ornith-mlx` symlink resolves again; GGUF is still absent (one model fits the reserve at a time). 
- **OpenCode drift handled:** the global binary moved 1.19.4→2.2.6, which broke the agent harness (`--dir`/`--pure` removed; `bash` tool renamed `shell`). Adapted `opencode_local.py`/`smoke_agent.py`/`report.py`; the JSON event schema is unchanged so F7 grading is unaffected. **Smoke re-validated 3/3** under v2.2.6 (read 27.1 s, edit_test 77.1 s, debug 145.7 s). D028.
- **F7 cohort complete:** the OpenCode-2.2.6 cohort (label `oc226-control`, Ornith MLX) finished 4/4, **2/4 end-to-end pass** — F7-B 985.0 s and F7-D 619.0 s pass; F7-A (.NET) and F7-C (Python) fail by hitting the 1200 s agent timeout (no `resource_abort`, no infra error — real non-completions). Explicitly **not comparable** to the historical 1.19.4 cohort (3/4; distinct OpenCode version, one run per task). The NuGet offline cache (deleted alongside the HF cache) was repopulated from nuget.org to unblock F7-A before the run. Raw: `benchmarks/results/tasks-mlx-oc226-control-20261108T100340.json`. See D029.
- **GitHub push resolved:** `github.com` DNS resolves again; the 403 was `osxkeychain` serving the stale `jcastros_crnova` token — fixed by using `gh` (owner account `full-stack-dev-johncastrosanabria`) as the git credential helper in this repo's local config. Commits `7dbda81` and `edd144a` pushed; `origin/main` at `edd144a`. See D029.
- **Deferred to a dedicated session:** the native official-core DEV optimization + held-out source-executor treatment (D026).

## Infrastructure event (not a quality result)

Between the 2026-10-25 checkpoint and this resume, the shared Hugging Face cache `~/.cache/huggingface` was cleared externally. This lab only ever stopped **owned** processes, never a cache deletion, so the removal is outside the experiment. Consequences:

- **Ornith 1.5 9B MLX 4-bit** and **Ornith 1.5 9B GGUF Q4_K_M** weights are absent; `models/ornith-mlx` and `models/ornith-gguf.gguf` are now dangling symlinks. `models/manifest.json` / `manifest-gguf.json` still record the pinned revisions for re-download.
- **Bonsai 2 27B** (ternary PTQ1_0) weights and the `llama-server` binary live in iCloud Drive (`~/Library/Mobile Documents/com~apple~CloudDocs/bonsai/bonsai-demo`), are intact and fully materialized (5.5 GiB, not evicted), and remain the **only locally runnable model** right now. Port 8085 (D014).

## Disk and cleanup

Free disk at resume was ~5.6 GiB — **below the D003/D008 8 GiB reserve**. Safe reclaim was limited to re-downloadable package caches (`uv cache clean`, `brew cleanup`); no user data touched. It recovered **negligible** space (still ~5.5 GiB free): there is no large *safe*-to-delete store on this host — `uv` keeps its in-use cache and Homebrew held little. The only large reclaimable space on the host (~20 GiB) is **unrelated user Docker data** — a `novahub-technical-evaluation` project (a .NET app + SQL Server data volume + whisper transcriber + mailpit, containers exited ~32 h ago), an older `default-no-608db` workspace, and the **running** `rembric` service on 8787. Per D002/D008 this lab does not delete user data; freeing that space is deferred to an explicit user decision (D027).

**Docker is not used for any inference or harness run** and will not be: Docker Desktop's Linux VM cannot reach Apple Metal, so an MLX/llama.cpp run inside it would measure a GPU-less path and invalidate any hardware comparison. This matches the standing no-container rule (D002, D006). WorkBuddy stays excluded for the same reason.

## What is measured vs. blocked

- **Completed this cycle:** the official pinned **source-executor F7 control** (Ornith MLX) — 1/4 artifact acceptance and 1/4 end-to-end pass (F7-D passes at 684.5 s; A/B/C fail at ~400–421 s, all tests immutable, no timeout, no infra error, each truncated at the 4096 output cap). Weaker than the separate global-OpenCode MLX cohort (3/4); distinct executors, not pooled. See [HARNESS2.md](HARNESS2.md) and D026. Raw: `benchmarks/results/tasks-mlx-official-source-control-F7-*.json`.
- **Synthesis added:** [FINDINGS.md](FINDINGS.md) — the evidence-grounded "best model and configuration for this MacBook Air M3 / 16 GB" answer, with the one-run-per-task and model/runtime/quant-confound caveats intact.
- **Deferred to a dedicated session:** DEV optimization and the held-out **source-executor treatment** (D026). MLX weights are restored and runnable (D028) and disk headroom is adequate (~20 GiB free), so this is no longer a resource block — it is a long model+agent run left for a focused session.
- **Deferred (host safety):** running Bonsai 27B now is possible but unwise at ~5.6 GiB free — earlier 27B runs drove swap to 8 GiB and disk to 8.7 GiB; starting from 5.6 GiB risks exhausting the disk. Defer live Bonsai runs until headroom is restored.
- **Still unexecuted (as before):** three independent repetitions per long F7 task/condition, seed blocks, thermal crossover and long-session soak; official model-backed Harness² benchmark adapters.

## Fixed experimental profile (unchanged)

Context 16384, output cap 4096, temperature 0.6, top_p 0.95, concurrency 1, KV quant none, one loaded model at a time (D012/D013). Bonsai disables top-k/min-p filters to match MLX, `--reasoning-budget 100 --cache-ram 512`. Ponytail 5.3.2 full applies to Codex implementation/review only; evaluated-model prompts stay frozen (D016).
