# V157 Answer-Blind Structural Rescue — Frozen Protocol

Frozen before any V157 outcome inspection.

Use the saved V155 step-2 first-loss checkpoints for the same three independent seeds. No weight updates. Same eight held-out inputs.

Controller is answer-blind: it may use only the previously learned structural grammar for that developmental lineage (outer wrapper delimiters and terminal suffix marker). It may not compute, search for, compare against, or construct the protected target answer during control.

Correct structural controller:
- Task A: if output is wrapped, remove the outer wrapper; then if it ends in the lineage suffix, remove that suffix.
- Task AB: if output is wrapped, remove the outer wrapper.
- Task ABC: leave output unchanged.

Causal ablation: apply the next seed's structural grammar instead of the correct seed's grammar. This permuted controller receives the same raw outputs and has the same transformation budget, but the wrong boundaries.

Verifier computes protected A/AB/ABC targets only after controller output is frozen.

Primary criterion: correct structural controller improves A and/or AB exact accuracy under frozen weights, while the permuted-grammar ablation fails to reproduce the gain. Strongest result is restoration of both A and AB without degrading ABC.
