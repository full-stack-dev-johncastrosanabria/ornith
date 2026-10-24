# Checkpoint — 2026-10-24, native experiments incomplete

Estimated overall progress: 35%. This is a work estimate, not a measured completion score. Main comparison: 2 of 12 planned non-GGUF task runs closed (17%): Ornith control A and B. Hardware, pinned MLX setup, native API/parser validation, 3/3 OpenCode tool cycles, fixture construction and the official deterministic Harness² demo are verified.

- F7-A control: no implementation, six external tests fail; 712.5 s, output limit4096, no API/installation error.
- F7-B control: artifact passes all three external tests and test hashes are preserved, but the agent timed out at1200 s. Artifact correctness and completed-agent productivity must be reported separately.
- C/D control, local Propose–Probe–Compose optimization and treatment, native MLX throughput counters, and final-profile Bonsai comparison remain unexecuted or interrupted. No quality score is assigned to an interrupted C workspace.
- GGUF is not downloaded: the Q4_K_M weights cannot preserve the required 8 GiB reserve. No runtime superiority conclusion is available.

After resuming, native MLX coincided with system swap increasing from3864 MiB to8018 MiB and free disk falling from12.67 GiB to8.72 GiB. The owned campaign92669, owned OpenCode92835 and owned MLX server92672 were stopped to protect the operating reserve. Existing unrelated services were left intact. Port8080 belongs to an unrelated service; the laboratory's Bonsai launcher/config now use8085. No Docker/VM commands were used to execute any experiment.

Heavy inference is held pending available host memory. Lightweight checks can continue. Future native runs include an 8 GiB disk guard; timeout recovery restarts only the owned model to prevent an abandoned generation contaminating the next task. A detached sequential campaign resumes missing task IDs and retains negative results rather than retrying until green.

Ponytail5.3.2 is installed from DietrichGebert/ponytail. Its full skill applies to Codex implementation/review, not to evaluated-model prompts, to preserve the experiment's fixed control.
