# V158 Experiential Map Rescue — Frozen Protocol

Frozen before V158 outcomes.

Goal: remove the final oracle from V157. The controller must infer its structural state map from prior verified developmental experience rather than receiving wrapper/suffix constants directly.

For each of the three independent lineages, provide only a small calibration record on training-domain strings containing verified A, AB, and ABC outputs for the same inputs. Infer:
- AB extension/suffix from A -> AB differences;
- ABC wrapper boundaries by locating AB inside ABC.

Freeze the inferred map before loading the held-out first-loss checkpoint.

Then, at the saved V155 step-2 checkpoint, apply the learned map answer-blind to the same eight held-out inputs:
- A: strip learned wrapper if present, then learned AB suffix if present;
- AB: strip learned wrapper if present;
- ABC: unchanged.

Protected held-out targets are not available to map inference or control and are used only by the final verifier.

Causal ablation: replace each lineage's calibration experience with the next lineage's verified experience, infer a structurally valid but wrong map, and apply it with the same controller.

Primary success criterion: learned-from-correct-experience map materially improves A/AB exact accuracy under frozen weights, while shuffled-experience map does not reproduce the gain and ABC is not degraded.
