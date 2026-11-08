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
