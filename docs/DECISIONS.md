# Decisions

- D001: Preserve all existing files and installations. Root was empty; initialized a new local Git repository. No remote or push.
- D002: Native macOS only; no Docker/VM/Linux or cloud model credentials. Unrelated running apps are not stopped.
- D003: Pin Ornith MLX revision a48173b246ac705be75c05bedf1a0666db522d53 and reuse shared HF cache. Downloader checks missing bytes plus 8 GiB reserve and watches live free disk.
- D004: Existing OpenCode 1.19.4, isolated XDG roots and official OPENCODE_CONFIG mechanism. Enabled-provider allowlist and same local small_model avoid implicit external model routes. Native sandbox adds enforcement beyond tool permission strings.
- D005: Official Harness² upstream 1cfe254e8d25b15f37048c3730134686abe60335 stays clean at harness2/upstream. Core package has no dependencies and its deterministic k1 sequential demo succeeds natively (2 tasks, 8 executions, 8 editor calls, 0 failed). It is not an Ornith improvement result.
- D006: WorkBuddy's Docker dependency is incompatible with this experiment. No full benchmark installer or cloud bridge is run. Official OpenCode substrate expects pinned source commit 23fb5e0516c99ac04a1aa46c193efda2e1b9bb24 and Bun, not the global binary. A global-binary integration must be labeled a local adapter/reproduction.
- D007: New public equivalent F7 fixtures because originals were not located in bounded searches; explicit provenance and no historical score equivalence.
- D008: GGUF runtime comparison is technically justified to answer runtime question, but its 5,780,090,816-byte Q4_K_M download plus build must preserve the same 8 GiB reserve. Recheck after MLX; do not sacrifice reserve or delete user data.
