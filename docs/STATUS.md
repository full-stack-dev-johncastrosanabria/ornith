# Checkpoint — 2026-10-24, native experiments incomplete

Estimated overall progress: approximately45–50%. This is a work estimate, not a measured completion score. Cleared-host comparison: 4 of 12 planned non-GGUF task runs closed (33%); the MLX control is complete and local Propose–Probe–Compose is running. Hardware, pinned MLX setup, native API/parser validation, 3/3 OpenCode tool cycles, fixture construction and the official deterministic Harness² demo are verified.

- F7-A cleared-host control: no implementation, six external tests fail; 507.4 s, output limit4096, no API/installation error. The earlier congested cohort took712.5 s and remains separate.
- F7-B control: artifact passes all three external tests and test hashes are preserved, but the agent timed out at1200 s. Artifact correctness and completed-agent productivity must be reported separately.
- F7-C cleared-host control: completed in826.9 s; all8 external tests pass. F7-D completed in1166.3 s and passes acceptance. Overall3/4 artifacts pass acceptance, while2/4 agent runs complete successfully. Local Propose–Probe–Compose optimization is running; treatment, native MLX throughput counters, and final-profile Bonsai comparison remain pending. No quality score is assigned to the earlier interrupted C workspace.
- GGUF is not downloaded yet. Disk availability now permits an attempt after the current campaign. `scripts/campaign_gguf.sh CAMPAIGN_PID` waits for that owned controller to finish, checks resources and absence of another server, then builds/downloads, validates API and3/3 tool cycles, and only then benchmarks. Validation failure stops this sequence. No runtime superiority conclusion is available.

After resuming, native MLX coincided with system swap increasing from3864 MiB to8018 MiB and free disk falling from12.67 GiB to8.72 GiB. The owned campaign92669, owned OpenCode92835 and owned MLX server92672 were stopped to protect the operating reserve. Existing unrelated services were left intact. Port8080 belongs to an unrelated service; the laboratory's Bonsai launcher/config now use8085. No Docker/VM commands were used to execute any experiment.

The user subsequently freed resources. Native checks at15:31 showed15.54 GiB free disk, memory-pressure free percentage82%, and903 MiB used swap; no lab inference port was active. The new cleared-host cohort runs all four tasks for each condition so timing comparisons do not mix the old congested A/B with new measurements. Earlier negative outcomes are retained, not selectively retried until green. The newly available disk also permits attempting the conditional GGUF phase after the MLX/Bonsai sequence.

Native runs include an 8 GiB disk guard; timeout recovery restarts only the owned model to prevent an abandoned generation contaminating the next task. A detached sequential campaign resumes missing task IDs within the named cohort. Raw JSON and stage checkpoints determine progress; no completion is claimed while the matrix is incomplete.

Ponytail5.3.2 is installed from DietrichGebert/ponytail. Its full skill applies to Codex implementation/review, not to evaluated-model prompts, to preserve the experiment's fixed control.
