# Checkpoint — 2026-11-08, resumed; MLX/GGUF weights externally cleared

The experiment remains **incomplete**. The main runtime/harness matrix (16/16 valid task outcomes) and the micro-rate repetitions stand as measured on 2026-10-25 and are unchanged; see [RESULTS.md](RESULTS.md), [DECISIONS.md](DECISIONS.md) (D001–D027) and git history for the full trail. This checkpoint records the resumed-session state only.

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
- **Paused (needs a user disk decision):** DEV optimization and the held-out **source-executor treatment** cannot run until MLX weights are re-downloaded under the 8 GiB reserve. Re-download (~5–6 GiB each) will not fit the current reserve without first freeing space — i.e. the user's Docker decision above, or another large reclaim they approve.
- **Deferred (host safety):** running Bonsai 27B now is possible but unwise at ~5.6 GiB free — earlier 27B runs drove swap to 8 GiB and disk to 8.7 GiB; starting from 5.6 GiB risks exhausting the disk. Defer live Bonsai runs until headroom is restored.
- **Still unexecuted (as before):** three independent repetitions per long F7 task/condition, seed blocks, thermal crossover and long-session soak; official model-backed Harness² benchmark adapters.

## Fixed experimental profile (unchanged)

Context 16384, output cap 4096, temperature 0.6, top_p 0.95, concurrency 1, KV quant none, one loaded model at a time (D012/D013). Bonsai disables top-k/min-p filters to match MLX, `--reasoning-budget 100 --cache-ram 512`. Ponytail 5.3.2 full applies to Codex implementation/review only; evaluated-model prompts stay frozen (D016).
