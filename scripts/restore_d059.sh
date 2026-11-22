#!/bin/zsh
# D059/D060 restore: runtimes, Harness² and pinned weights for the oc232-nodocker cohort.
# Weights go to Disco 2 through ~/Developer/LocalLLMs. Run with no lab server active.
set -eu
ROOT=${0:A:h:h}
cd "$ROOT"
M="$HOME/Developer/LocalLLMs"
[[ $(uname -s) == Darwin && $(uname -m) == arm64 ]] || exit 1
[[ -d "$M/" ]] || { echo 'Disco 2 is not mounted (~/Developer/LocalLLMs).'; exit 1; }
benchmarks/.venv/bin/python -c 'import sys; sys.path.insert(0,"scripts"); from server import active; from memory import require_space; active(); require_space()'
# The memory guard measures Disco 2; uv caches and swap live on the internal disk, so check it too.
(( $(df -k / | awk 'NR==2{print $4}') > 8*1024*1024 )) || { echo 'Internal disk below the 8 GiB reserve.'; exit 75; }
LOG="$ROOT/logs/restore-d059-$(date +%Y%m%dT%H%M%S).txt"
echo "D059 restore $(date -u +%FT%TZ)" > "$LOG"

echo '== Harness² (pinned upstream + venv)'
zsh scripts/setup_harness2.sh
echo "harness2 $(git -C harness2/upstream rev-parse HEAD)" >> "$LOG"

echo '== Lab llama.cpp for Ornith GGUF (same steps as setup_gguf.sh, without its HF-cache download)'
mkdir -p runtimes/gguf
[[ -f runtimes/gguf/requirements.txt ]] || git show 31efacb^:runtimes/gguf/requirements.txt > runtimes/gguf/requirements.txt
[[ -d runtimes/gguf/.venv ]] || uv venv -q --python 3.12 runtimes/gguf/.venv
uv pip install -q --python runtimes/gguf/.venv/bin/python -r runtimes/gguf/requirements.txt
REV=d327bf1f0780f87b8c01b367b61853b0c291d7c4
SRC="$ROOT/runtimes/gguf/llama.cpp"
if [[ ! -d "$SRC/.git" ]]; then
  git clone --no-checkout --depth 1 https://github.com/ggml-org/llama.cpp.git "$SRC"
  git -C "$SRC" fetch --depth 1 origin "$REV"
  git -C "$SRC" checkout --detach "$REV"
fi
[[ $(git -C "$SRC" rev-parse HEAD) == "$REV" && -z $(git -C "$SRC" status --porcelain) ]] || { echo 'Unexpected llama.cpp checkout; inspect it first.'; exit 1; }
CM="$ROOT/runtimes/gguf/.venv/bin/cmake"
# D059: make breaks on the space in "Disco 2" (Xcode lives there too); Ninja quotes paths.
# The prebuilt web UI download came back incomplete; the lab only uses the HTTP API, so no UI is embedded.
uv pip install -q --python runtimes/gguf/.venv/bin/python ninja==1.13.2
[[ -f "$SRC/build-nossl/build.ninja" ]] || rm -rf "$SRC/build-nossl"
rm -rf "$SRC/build-nossl/tools/ui/dist"
"$CM" -G Ninja -DCMAKE_MAKE_PROGRAM="$ROOT/runtimes/gguf/.venv/bin/ninja" -S "$SRC" -B "$SRC/build-nossl" -DLLAMA_USE_PREBUILT_UI=OFF -DGGML_METAL=ON -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_TESTS=OFF -DLLAMA_OPENSSL=OFF
"$CM" --build "$SRC/build-nossl" --config Release --target llama-server -j 2
shasum -a 256 "$SRC/build-nossl/bin/llama-server" | tee -a "$LOG"
"$SRC/build-nossl/bin/llama-server" --version 2>&1 | tee -a "$LOG"

echo '== PrismML llama.cpp for Bonsai (release used since D054)'
TAG=prism-b10772-e8fd209
B="$M/bin/bonsai-llama.cpp-mac"
if [[ ! -x "$B/llama-server" ]]; then
  T=$(mktemp -d "$ROOT/logs/bonsai-bin.XXXXXX")
  curl -fL --progress-bar -o "$T/bin.tar.gz" "https://github.com/PrismML-Eng/llama.cpp/releases/download/$TAG/llama-$TAG-bin-macos-arm64.tar.gz"
  shasum -a 256 "$T/bin.tar.gz" | tee -a "$LOG"
  mkdir -p "$B"
  # Same extraction as bonsai-demo/scripts/download_binaries.sh.
  tar -xzf "$T/bin.tar.gz" -C "$B" --strip-components=1 2>/dev/null || tar -xzf "$T/bin.tar.gz" -C "$B"
  rm -rf "$T"
  xattr -cr "$B"
  for f in "$B"/llama-*; do [[ -f $f ]] && codesign -s - --force --timestamp=none "$f"; done
fi
"$B/llama-server" --version 2>&1 | tee -a "$LOG" | grep -q 10772 || { echo 'Bonsai binary is not build 10772.'; exit 1; }
shasum -a 256 "$B/llama-server" | tee -a "$LOG"

echo '== Pinned weights (sha256 checked against the Hugging Face LFS hashes)'
fetch() {  # repo file revision sha256 destination
  uvx -q --from huggingface-hub==2.3.0 --with hf-xet==1.7.0 hf download "$1" "$2" --revision "$3" --local-dir "$5"
  echo "$4  $5/$2" | shasum -a 256 -c | tee -a "$LOG"
  echo "$1@$3 $2" >> "$LOG"
}
fetch ornith-ai/Ornith-1.5-9B-GGUF Ornith-1.5-9B-Q4_K_M.gguf abdd624b12ebf020b767fff532ff44fe552b28c3 70c112196e0b7023803c9762752e46d29e612a92c83f995bc3ba1ceb07e8fab6 "$M/ornith-1.5-9b-gguf"
fetch prism-ml/Ternary-Bonsai-2-27B-gguf Ternary-Bonsai-2-27B-PTQ1_0.gguf 839bd57023c1558945afea70a74fa83c054f35f9 53107f530aa52eb00912263ab1ee29bd199261c87cd7b4ad4ca1318c1fe33ee3 "$M/bonsai-2-27b"
fetch prism-ml/Ternary-Bonsai-2-9B-gguf Ternary-Bonsai-2-9B-PTQ1_0.gguf 82265ccc78ddaac4700286a35e9badcc32376dd9 3561df7ac7d26a71ffa991ac2db740b10841c3a350aa2676ccd3ff5d428b4e8b "$M/bonsai-2-9b"
[[ -L models/bonsai2-9b.gguf ]] || ln -s "$M/bonsai-2-9b/Ternary-Bonsai-2-9B-PTQ1_0.gguf" models/bonsai2-9b.gguf
ls -lL models/ornith-gguf.gguf models/bonsai2-9b.gguf "$M/bonsai-2-27b/Ternary-Bonsai-2-27B-PTQ1_0.gguf" | tee -a "$LOG"

echo '== D061: JUnit 5 jars for F8-E (local Maven cache, sha1-checked)'
zsh scripts/setup_java_junit.sh | tee -a "$LOG"
echo "Restore complete; evidence in $LOG"
