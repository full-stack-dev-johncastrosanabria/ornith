# Ornith local laboratory

- Native macOS Apple Silicon only. No Linux, containers, VMs or cloud inference, optimization or evaluation.
- Preserve Bonsai and all global configurations. Work exclusively inside this laboratory.
- One loaded inference model at a time. Use scripts/server.py and stop it before switching.
- Downloads require a live space check and at least 8 GiB remaining free.
- Never modify acceptance tests. Do not access solutions or hidden rubrics.
- Separate official Harness², local adapters and methodology reproductions in all reports.
- An infrastructure failure is not a model quality failure. Missing measurements are N/E, never zero.
- Keep raw evidence, pinned dependencies, clean fixture copies and independent test results.
- Do not claim completion until model and agent measurements are reproducible.

## Discovery and output

- `/graphify` requires reading `~/.Codex/skills/graphify/SKILL.md` first.
- Prefer codebase-memory MCP for code discovery: list_projects/index_status, search_graph, trace_path, get_code_snippet, then check_index_coverage for all evidence paths. Default tier: Verify. If the service is unavailable or coverage is insufficient, record it and inspect exact source locally.
- For many files, JSON, logs and command results, use context-mode ctx_execute/ctx_batch_execute to compute a concise result. Index large documents once and search targeted slices.
- Read-only fixture tests are public acceptance specifications; do not infer historical score equivalence.
