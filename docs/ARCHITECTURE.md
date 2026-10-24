# Native architecture

Verified 2026-10-24: MacBook Air Mac15,12, Apple M3 (8 CPU / 8 GPU cores), 16 GB unified memory, macOS 27.2 build 26B118, Metal 4. Initial available disk: 18,467,627,008 bytes (17.20 GiB). Initial system swap used: 1260.94 MiB. No inference process detected initially. Existing unrelated applications were left running.

Python 3.12.13 is already managed by uv. Independent virtual environments: runtimes/mlx/.venv (MLX-LM), harness2/.venv (upstream core, no optional cloud bridge), benchmarks/.venv (public acceptance tests). Existing Git, uv, Node 26.12.1, .NET SDK 10.0.201 and OpenCode 1.19.4 are reused.

```text
OpenCode 1.19.4 (isolated XDG state, native Seatbelt sandbox)
  -> localhost only -> one native inference runtime
       :8082 MLX-LM / Metal / Ornith MLX 4 bit
       :8083 independent llama.cpp / Metal / Ornith Q4_K_M (conditional)
       :8080 existing PrismML llama-server / Bonsai PTQ1_0
External Python/.NET acceptance evaluation -> JSON evidence -> report
Harness² upstream deterministic demo is separate from local Ornith experiments.
```

Weights reuse ~/.cache/huggingface/hub through symlinks. No model is committed or duplicated. MLX repository revision a48173b246ac705be75c05bedf1a0666db522d53; architecture qwen3_5, 32 hybrid layers, affine 4-bit group64; Qwen2 tokenizer, qwen3_coder tool parser, dedicated Jinja chat template. No trust_remote_code requested. KV quantization is not enabled.

The initial runtime cache budget is 512 MiB and concurrency is 1. MLX-LM does not expose a server --ctx-size option in the installed version. `scripts/mlx_server.py` is an explicit local adapter around pinned MLX-LM 0.32.2: it checks the exact upstream-tokenized input plus requested output against 8192 and restricts model selection to the pinned local weights. It leaves generation, kernels, reasoning and tool parsing upstream. OpenCode advertises the same 8192 window and a 1536 output cap. The negative test rejects 9010 input +128 output and confirms server health. The error text contains context_length_exceeded so OpenCode can recognize overflow and compact (the first wording did not; affected preflight attempts are retained and excluded from quality scoring). Upstream returns HTTP404 for generation exceptions; non-200 status alone is not a compatibility guarantee.

The native sandbox denies writes outside each workspace and its isolated state, denies writes to public tests, denies reads of other home-directory data, and denies non-loopback network traffic. Its configuration and enforcement are tested independently of model outcomes. Dependencies may be downloaded during setup, never by model inference. No global OpenCode file is overwritten.

Graph and Rembric services were unavailable at session start (transport closed / fetch failed); source inspections use bounded filesystem fallback.
