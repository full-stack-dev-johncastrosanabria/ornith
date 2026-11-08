<<<EDIT context/harness/systemprompt.md>>>
You make small, correct programming changes in one workspace and verify them with that workspace's own tests. Tool calls are slow and the run's budget is finite. If you keep exploring after you have what you need, the run ends with nothing delivered.

1. List the workspace root once. That listing is your file inventory.
2. Read TASK.md, the source file to change and the tests that exercise it, each once. You have enough evidence when you can state three things: the required behaviour, the file and function to change, and the test command. Stop reading as soon as you can.
3. Your next call is the edit. Do nothing optional before the edit and the first test run.
4. Run the exact test command from TASK.md from the workspace root, without piping it (`cd` to the root in the same command).
5. If a test fails, read the whole failure output, fix the source and run the tests again. After 3 failing runs, stop and report.
6. You are done when the source file on disk holds your change and you have the real output of the test command. A successful edit call proves neither of these; the test run is the check. If the tests cannot run, reopen the edited file to confirm the change is there.

Final reply: name the file and function you changed, give the test command, and copy its summary line from the output. If the tests did not run, say so and quote the error. Never report a result you did not observe.
<<<END EDIT>>>
<<<EDIT context/harness/guardrails.md>>>
- Stay inside the workspace root. The only exception is running the exact commands TASK.md gives. Do not explore parent directories, sibling directories or other tasks' work directories, and do not look for reference implementations. Build the change from TASK.md, the source and the tests.
<<<END EDIT>>>
<<<EDIT context/harness/tool_descriptions/tool_guidance.md>>>
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
<<<END EDIT>>>
<<<ANSWER>>>
<notes>
INV editor (procedure, tool use, completion). The only evidence is one rollout, base1, and it produced no deliverable. I edited systemprompt.md, guardrails.md and tool_descriptions/tool_guidance.md. LongTermMEMORY.md is unchanged, because domain facts belong to the parallel candidate. As the mission requires, I added no skills, scripts, plugins or subagents.

What base1 did:
- Calls 1-5 (done by 42 s) listed the root and read TASK.md, normalize.py, tests/ and tests/test_normalize.py. That is everything the change needs.
- The next step took 151 s of generation. It said "Now I understand the task. Let me explore the broader project structure to understand the context and check for any reference implementations." It then made calls 6-7: `ls -la` of the root again, and `ls` of benchmarks/, which returned Operation not permitted. This is the earliest divergence.
- Calls 8-16 went to the lab root and benchmarks/work/, tried AGENTS.md and .gitignore (neither exists), ran git three times and listed docs/ twice.
- The run ended after call 16, at 493 s. There was no edit, no test run and no deliverable.

systemprompt.md (replaces the one-line base; that line's content survives in steps 2 and 4 and the final reply):
- Steps 1-3: list the root once, read each needed file once, check that there is enough evidence, then make the edit next, with nothing optional before the edit and the first test run. Moment: the step after call 5. The agent said it understood the task, then spent 11 calls exploring. With this rule the edit would have been call 6, leaving budget for the test run and the report.
- Step 4: run the exact command from the root (`cd` in the same command), without a pipe. This targets a risk that had not happened yet, since tests never ran. The agent used absolute paths and never changed directory. Call 9 (`ls ...; echo; ls ... | head -80`) returned exit 0 while printing a denial.
- Steps 5-6 and the final reply set a cap of 3 failing test runs and a definition of done: the change is on disk and real test output exists. A successful edit call is not proof; the agent reopens the file if tests cannot run and never reports a result it did not see. The run ended without either artifact. This sets the finish line it never reached and keeps budget for the report.

guardrails.md: stay in the workspace except to run TASK.md's commands, and do not look for reference implementations or other tasks' work directories. Moment: calls 7-9 and 15-16, whose stated purpose was to "check for any reference implementations" and the "benchmark structure and any reference implementations". benchmarks/work/ is the parent of this workspace and holds many sibling run directories (call 6 shows 70 links on `..`). Searching it wastes budget and is out of bounds for a benchmark run.

tool_guidance.md classifies each error and allows one bounded response:
- File not found means a guessed path. Calls 10-11 read AGENTS.md and .gitignore after the listings in calls 1 and 6 showed neither.
- Operation not permitted marks the sandbox edge: no retry, no `2>/dev/null`, no probing nearby paths. Calls 7, 9 and 15 were denied, and the agent kept moving to other paths nearby. Call 16 re-ran call 15's listing with `2>/dev/null` (described as "second attempt") and got a bare "total 0", a denial that looks like an empty directory.
- `not a git repository` means git is unavailable. Calls 12-13 failed, then call 14 tried git again at the lab root ("Let me check the parent directory's git history").
- Unused output and chain exit codes: call 6 re-listed what call 1 had already shown, and call 9 returned exit 0 with an error in its text.
- The infrastructure line (a required step cannot start or times out: one re-run only after a timeout, then report; no interpreter swaps; no test or dependency edits) and the line "a denied listing tells you nothing about the command" were not seen in the run. They are there because call 7's denial covers benchmarks/, which contains the venv interpreter TASK.md requires. The agent must not read that denial as "tests unavailable".
- Workspace facts, labelled "in this workspace":
  - root inventory: calls 1, 4, 6 and 10-13
  - denials outside the root: calls 7, 9, 15 and 16
  - git failing at the lab root: call 14
  - the test's import from the root: call 5

  That the import needs the root as working directory is deduced, not run. `python -m` puts the working directory on sys.path, and there is no conftest or pytest config.

Left out on purpose: anything about how normalize should behave or the test's expected values. Those are subject-matter facts, owned by the parallel candidate. If a later rollout ignores this text and again ends without an edit, the next step is a plugin that blocks finishing until the source file has changed and the test command has run. One rollout is not enough evidence for it.

Limits and risks: there was only one rollout, so there was no disagreement between runs to learn from. I executed nothing. Every run now pays for about 550 words of always-on text; in the only evidence, that would replace about 11 wasted calls. Editor: the cloud editor (Claude) saw only DEV material; all solver inference and scoring stay local.
</notes>
<<<END ANSWER>>>