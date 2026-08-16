# V152B — Exact-O1 and R10 precedence apparatus addendum

Frozen: 2026-08-16 NZST, after V152A exited before any model call.

V152A revealed two apparatus-only defects:

1. `v152_exploration_support_separator.py` imported the original V151 experiment directly, reintroducing its paraphrased O1 literal. V151B had instead used `v151_exact_o1_runner.py` to bind the immutable V149 O1 object before execution.
2. the V152 wrapper classified an empty-response inner R10 as `R10_INSUFFICIENT_PROPOSAL_DIVERSITY` because diversity was checked before propagating the inner R10.

V152B changes only those apparatus facts:

- import `v151_exact_o1_runner` before V152 execution so the experiment module receives the exact frozen O1 object used by V151B;
- propagate inner `R10_INCONCLUSIVE` before evaluating the diversity gate.

No scientific parameter changes from V152: temperature remains 0.7; same model, T1/T2, exact O1, raw T1 evidence, shams, paired seeds, two-call budget, context resolver, structured-edit protocol, native verifier, diversity criterion, arm classifier, stopping rule, and claim boundary.

No V152/V152A model sample occurred before this addendum was frozen.