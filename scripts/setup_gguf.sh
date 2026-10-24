#!/bin/zsh
set -eu
ROOT=${0:A:h:h}
cd "$ROOT"
[[ $(uname -s) == Darwin && $(uname -m) == arm64 ]] || exit 1
harness2/.venv/bin/python -c 'import sys; sys.path.insert(0,"scripts"); from server import active; from memory import require_space; active(); require_space()'
[[ -d runtimes/gguf/.venv ]] || uv venv --python 3.12 runtimes/gguf/.venv
uv pip install --python runtimes/gguf/.venv/bin/python -r runtimes/gguf/requirements.txt
REV=d327bf1f0780f87b8c01b367b61853b0c291d7c4
SRC="$ROOT/runtimes/gguf/llama.cpp"
if [[ ! -d "$SRC/.git" ]]; then
  git clone --no-checkout --depth 1 https://github.com/ggml-org/llama.cpp.git "$SRC"
  git -C "$SRC" fetch --depth 1 origin "$REV"
  git -C "$SRC" checkout --detach "$REV"
fi
[[ $(git -C "$SRC" rev-parse HEAD) == "$REV" && -z $(git -C "$SRC" status --porcelain) ]] || { echo 'Preserving unexpected or modified llama.cpp checkout; inspect it first.'; exit 1; }
GGUF_CMAKE="$ROOT/runtimes/gguf/.venv/bin/cmake"
"$GGUF_CMAKE" -S "$SRC" -B "$SRC/build" -DGGML_METAL=ON -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_TESTS=OFF
"$GGUF_CMAKE" --build "$SRC/build" --config Release --target llama-server -j 2
"$ROOT/runtimes/mlx/.venv/bin/python" scripts/download_model.py --gguf
