# Independent llama.cpp — conditional, not installed

The comparison is justified by the runtime research question, but the Q4_K_M weights are 5,780,090,816 bytes. The measured post-MLX free space would leave only about 6.7 GiB after downloading them, below the mandatory 8 GiB reserve, before build dependencies. No GGUF download/build/inference was performed and no Bonsai fork was changed.

When sufficient disk exists, use a **separate pinned checkout** of https://github.com/ggml-org/llama.cpp at `runtimes/gguf/llama.cpp`, build Metal with CMake (`-DGGML_METAL=ON`, release, target llama-server), record the SHA and CMake version, then download **only** `Ornith-1.5-9B-Q4_K_M.gguf` from `ornith-ai/Ornith-1.5-9B-GGUF` revision `abdd624b12ebf020b767fff532ff44fe552b28c3` into the shared cache and link it as `models/ornith-gguf.gguf`. Check reserve immediately before and throughout download. No vision projector is required for these text tasks.

The launcher expects the independent binary at `runtimes/gguf/llama.cpp/build/bin/llama-server` and starts one slot on localhost:8083, context8192, full GPU offload, Jinja tool parsing, temp0.6/top_p0.95. Re-query `/v1/models`; perform API parser tests and 3/3 actual OpenCode cycles before any task scores. Those settings and the candidate config have not been validated in this laboratory.

Run identical fresh F7 task copies and the same short requests as MLX. Runtime-specific quantization (MLX affine4 vs GGUF Q4_K_M) is an unavoidable confound: do not attribute a quality difference solely to runtime. Never load the two model variants concurrently.
