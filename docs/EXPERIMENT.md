# Protocol

Status: in progress; no claim of experimental completion.

After the user freed host resources, a complete `cleared-host` cohort repeats all four tasks per condition with the existing fixed inference parameters. The old congested A/B outcomes remain separate. This is an environmental block, not selective rerunning of failed tasks. Reporting selects one named cohort per condition and does not fill its missing tasks from older blocks. Use the newly measured cohort's short API runs as well; retain initial compilation/warmup variation.

Priority: externally verified correctness, total task time, then decode throughput. Targets (15 t/s, 3/3 tool cycles, 4/4 F7, >=30% task-time reduction, no OOM or sustained model-caused swapping) are hypotheses.

## Controls

- Sequential execution, one loaded model, fresh workspace and session per task.
- Fixed task budgets: at most12 OpenCode steps and1200 s per F7 run; DEV probes use600 s. The4096 output cap includes reasoning. A limit/timeout outcome describes this bounded profile, not model capability with unlimited reasoning or a larger context.
- Initial integration preflights used 8192 context and a 1536 OpenCode output cap. After 3/3 tool cycles, first validate context16384 with the output cap unchanged, then increase only the output cap to4096. Final task matrix fixes context16384/output4096 across conditions; temperature .6/top_p .95, top_k0/min_p0 (explicit on final llama.cpp, defaults on MLX), no KV quantization. Bonsai uses FAST reasoning-budget100, not its historical QUALITY profile. Do not pool initial 8K short measurements with the final 16K baseline or present these multi-stage setup differences as a one-variable speed experiment.
- Preserve runtime/model revision, exact argv, config hash, acceptance hashes, raw events, independent tests and memory snapshots.
- Three repetitions of short microbenchmarks; report medians and min/max. Do not infer prefill speed by dividing prompt tokens by TTFT. Runtime-reported prefill/decode timings are separate from transport TTFT and wall time.
- Distinguish cached and cold input. The short API protocol varies a leading nonce and sends cache_prompt=false; support of this flag varies by runtime. MLX direct benchmarks must state whether prompt KV cache is reused.
- Initial warmup/compilation is retained and identified; no undocumented exclusions.
- Memory is unified; RSS and Metal allocations are different measurements and must not be summed. Existing swap does not by itself demonstrate model-caused swapping.

## Fixtures and grading

Historical Bonsai F7 reports were found, but original task sources were not located in the inspected directories or Spotlight. The versioned F7-A/B/C/D fixtures here are newly created public equivalents, not those originals. Never compare their scores directly to the historical 4/4. F7-A: ASP.NET Core order validation and xUnit. F7-B: FastAPI/Pydantic item validation and pytest. F7-C: mapping refactor with behavioral and AST checks. F7-D: multi-file discount/tax repair.

The manifest pins source hashes. Tests are public, immutable to the agent, and rerun independently. Restore/build/tool failures are infrastructure outcomes, not failures of model quality. Report acceptance counts and structural checks separately. Passing these bounded tests does not prove production quality.

DEV is the only optimization fixture. Final F7 tasks must not be supplied to the proposer or composer. An adapted Propose-Probe-Compose run uses k=1 sequential, one worker, same Ornith model for proposer/composer/solver. Save proposal and composition, measure optimization cost separately, freeze the selected system guidance, then evaluate fresh F7 workspaces with and without it. This local reproduction is not an official Harness² model-backed benchmark.

No task is allowed to access external solutions or hidden rubrics. All network during agent execution is loopback only.

Once dependency setup populated the pinned NuGet cache, fresh C# workspaces restore exclusively from `~/.nuget/packages` with NuGet audit disabled for offline evaluation; agent and external tests use `--no-restore`. Missing cached packages are infrastructure failures, not a reason to contact a remote provider during a measured task. The native campaign holds an idle-sleep assertion with `caffeinate -i -w <owned PID>`; it ends with the campaign and changes no global power settings.
