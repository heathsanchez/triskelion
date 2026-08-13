# V74 — Held-out Mathematical Grammar Transfer

Verdict: `MIXED_MATH_GRAMMAR_TRANSFER_V74`

Protocol: all five `math` events were removed before learning motifs and transition statistics. Training used the 46 non-math events only. Candidate operator programs of the same length as each held-out successful math trace were exhaustively ranked. Controls shuffled operator order within every training trace while preserving each trace's operator multiset and length.

Key result:
- Learned motifs from non-math: `CONSTRAIN→SELECT→RETAIN`, `CONSTRAIN→SELECT`, `RELATE→COMPOSE`, `SELECT→RETAIN`, `TRANSDUCE→CONSTRAIN`.
- Macro grammar held-out math mean percentile: **0.978831**.
- Primitive transition grammar held-out math mean percentile: **0.978947**.
- Macro MRR: **0.7333**.
- Primitive MRR: **0.8667**.
- All five held-out math traces were top-10 under both.
- Shuffled-order control mean percentile: **0.896659**.
- Shuffle p-value for macro percentile: **0.03498** (fails frozen p<=0.01 gate).

Interpretation: the learned cross-domain operator-order structure transfers strongly into mathematical traces, but the V72 macro/chunk layer does not improve over the primitive operator grammar in this test. Therefore V74 does **not** support the claim that the discovered motifs themselves improve mathematical processing. The residual suggests a different hypothesis: the primitive typed operator grammar may already contain most of the transferable mathematical control signal, and chunking may be useful mainly for bounded search/consolidation rather than route ranking.

Scientific consequence: do not count V74 as a positive motif-to-math result and do not tune the test after seeing the outcome. Any next mathematical experiment should explicitly target the primitive-alphabet hypothesis, not silently re-test the failed macro advantage.

Actions run: `31743038770`, job `math-grammar-v74`. Artifact SHA-256: `6767cda6ec0e22f25301848d8d31129574283de586205fb6085005b5edc01d07`.
