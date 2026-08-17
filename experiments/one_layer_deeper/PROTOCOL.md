# MathGraph / Metalogic Labs — One Layer Deeper

Primary question: does a shared learned transition operator improve certified serial continuation before adding optimizer, loss, or routing complexity?

Frozen substrate: tilde-research/one-layer-deeper public evaluator and official baseline.

## E0000 baseline
Official one-block Transformer + AdamW.

## E0001 tied recurrence
Observation: the task requires serial continuation but baseline applies its learned block once.
Hypothesis: reusing the same learned block creates a reusable transition substrate and should improve depth-profile continuation.
Rival: gains, if any, are merely additional compute/depth and do not transfer across depth or N.
Intervention: change only forward computation from one application of the same Block to four applications; parameters and optimizer otherwise unchanged.
Prediction: on Easy E1, E0001 should improve held-out/depth-profile performance relative to E0000, with particular interest in first certified T. It may complete fewer training steps because of the same 60 s clock.
Kill criterion: no improvement in certified Max T and no meaningful improvement at the first uncertified depth rung after accounting for completed training steps.
Promotion criterion: any increase in certified Max T; otherwise >=10 percentage-point increase at the first uncertified rung that survives a second public world before promotion.

No Medium intervention is licensed from a single Easy world. Hard remains protected and is not used for search.
