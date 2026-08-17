# MathGraph / Metalogic Labs — One Layer Deeper

Primary question: does a shared learned transition operator improve certified serial continuation before adding optimizer, loss, or routing complexity?

Frozen substrate: tilde-research/one-layer-deeper public evaluator and official baseline.

## E0000 baseline
Official one-block Transformer + AdamW.
Hosted H100 Easy E1 result: score 1.33%; Max T none certified; OOD N Max T none certified.

## E0001 tied recurrence
Observation: the task requires serial continuation but baseline applies its learned block once.
Hypothesis: reusing the same learned block creates a reusable transition substrate and should improve depth-profile continuation.
Rival: gains, if any, are merely additional compute/depth and do not transfer across depth or N.
Intervention: change only forward computation from one application of the same Block to four applications; parameters and optimizer otherwise unchanged.
Prediction: on Easy E1, E0001 should improve held-out/depth-profile performance relative to E0000, with particular interest in first certified T. It may complete fewer training steps because of the same 60 s clock.
Kill criterion: no improvement in certified Max T and no meaningful improvement at the first uncertified depth rung after accounting for completed training steps.
Promotion criterion: any increase in certified Max T; otherwise >=10 percentage-point increase at the first uncertified rung that survives a second public world before promotion.
Hosted H100 Easy E1 result: score 1.33%; Max T none certified; OOD N Max T none certified.
Decision: the primary prediction failed. E0001 is not promoted. Aggregate score and certification are exactly unchanged from E0000, so simple 4x tied recurrence has no demonstrated benefit. The unresolved rival is that spending 4x forward compute during training may reduce the number/effectiveness of updates enough to hide any evaluation-time continuation benefit.

## E0002 train-1 / eval-4 tied recurrence separator
Observation: E0001 changed both available serial computation and the amount of compute consumed per training example under a fixed 60 s budget.
Hypothesis: the baseline block may contain a partially reusable transition, but training it through four repeated applications sacrifices too much update throughput. If so, preserving baseline training (one block application) while reusing the same learned block four times only at evaluation should improve depth continuation without reducing training throughput.
Rival: the learned baseline block is not a reusable transition operator; repeated application at evaluation will not help and may corrupt the representation.
Intervention: exact E0000 model/optimizer/training behavior; when model.training is false, apply the same block four times instead of once. No new parameters, optimizer changes, losses, schedules, or data changes.
Prospective prediction: on Easy E1, E0002 should exceed E0000's 1.33% aggregate score and/or certify a first depth rung. Strong evidence is any certified Max T > none; weak evidence is >=10 percentage-point improvement at the first uncertified rung if exposed by the evaluator.
Kill criterion: no certified-depth gain and no meaningful aggregate or first-uncertified-rung gain relative to E0000.
Promotion criterion: any certified Max T gain; otherwise a >=10 percentage-point first-uncertified-rung gain must survive a second Easy world before becoming a law.

No Medium intervention is licensed from a single Easy world. Hard remains protected and is not used for search.
