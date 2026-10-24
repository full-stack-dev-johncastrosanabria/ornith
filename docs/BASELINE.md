# Bonsai baseline

Read-only installation located at `~/Library/Mobile Documents/com~apple~CloudDocs/bonsai/bonsai-demo`. Existing native binary `bin/mac/llama-server` and `models/bonsai2-gguf/27B/Ternary-Bonsai-2-27B-PTQ1_0.gguf` are reused directly. No existing launcher or config is called, because those write logs/PIDs outside this laboratory. Our launcher stores all output here. No projector is loaded for text tasks.

Historical reports in sibling `bonsai-optimization/REPORTES-F1-F8.md` and `RESULTS.md` describe 4/4 F7, FAST budget100, QUALITY medium and 5–7 t/s. These are historical observations, not current comparison evidence; original fixture sources have not been located. Earlier reports also record substantial swap and interrupted runs.

New controlled short baseline: context8192, one slot, Metal full offload, FP16 KV, temp .6, top_p .95, reasoning budget100, cache-ram512 MiB. It deliberately differs from the historical 24576/1.0/2048 MiB profile; use the saved argv rather than treating these as identical settings.

Three 128-token streaming requests were measured. Decode median 6.8304 t/s (6.8067–6.8385), runtime prefill median 24.6213 t/s (23.1268–24.8385), TTFT median 4.4239 s (4.3774–4.6456), wall median 22.9959 s (22.9704–23.3022). All three prompts show zero cached input tokens. Raw evidence: `benchmarks/results/micro-bonsai-20261024T100001.json`.

OpenCode and F7 measurements are still in progress. No conclusion about Ornith productivity can be drawn from this baseline alone.
