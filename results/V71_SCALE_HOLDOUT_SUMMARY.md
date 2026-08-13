# V71 Whole-Scale Grammar Transfer

Verdict: PASS_SCALE_HOLDOUT_GRAMMAR_V71

The operator grammar was trained with one entire predeclared scale absent at a time.

Held-out scale results:
- architecture: 18.97% compression; next-op 43.59% vs 23.08% majority
- control: 30.00% compression; next-op 50.00% vs 16.67% majority
- representation: 36.36% compression; next-op 69.23% vs 15.38% majority
- task: 23.08% compression; next-op 45.45% vs 27.27% majority

Aggregate:
- whole-scale compression: 23.9437%
- shuffled-training compression mean: 12.3676%
- compression empirical p: 0.00049975
- whole-scale next-op accuracy: 48.3516%
- majority accuracy: 23.0769%
- shuffled-order next-op mean: 24.6665%
- next-op empirical p: 0.00049975

All frozen gates passed.

Interpretation boundary: this is internal evidence from the manually normalized 51-event corpus. It supports cross-scale grammatical structure, not universality. Next gate: infer a minimum-description-length motif basis without fixing the number or names of higher-order units.

Actions run: 31742125256
Artifact SHA-256: 4508a8510366f021cfcb98a719d4b629cfb8005a1d3bc3b63470013a0216462c
