# When a tool result fails or surprises you, classify it and respond once

- `File not found` on a read means bad input: you guessed a path. Use the listing you already have and guess no more names.
- `Operation not permitted` outside the workspace marks the edge of the sandbox, and that edge stays fixed for the whole run. Do not retry the command, rephrase it or run it again with `2>/dev/null`; that only hides the denial behind an empty-looking `total 0`. Do not probe nearby paths either. Return to the workspace.
- `not a git repository` means git is not available here. Do not use git again this run; reopen files to check a change.
- Before calling a tool, check whether an earlier result already answers the question. A command chain joined with `;` or `|` reports only the last command's exit code, so an exit code of 0 can hide an error. Read the text.
- If a required step (the edit or the test command) cannot start ("not found", "permission denied") or times out, treat it as an infrastructure failure. After a timeout, run it once more with a longer timeout. Otherwise report the exact error. Do not switch to another interpreter, edit tests or dependency files, or claim a result.
- A denied directory listing tells you nothing about whether the TASK.md command under that directory will run. Run the command and judge it by its own output.

# In this workspace (seen in the base run)
- The root starts with only normalize.py, TASK.md and tests/test_normalize.py. There is no git repository, AGENTS.md, .gitignore, conftest.py, pytest config or hidden file.
- Outside the root, listing the lab's benchmarks/, benchmarks/work/ and docs/ directories is denied, and git fails even at the lab repository root. Nothing outside the root is needed except the interpreter TASK.md names.
- tests/test_normalize.py does `from normalize import normalize`, so its import works only when the TASK.md command runs from the root.
