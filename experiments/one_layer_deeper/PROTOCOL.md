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
Hosted H100 Easy E1 result: score 5.33%; Max T none certified; OOD N Max T none certified.
Decision: E0002 shows a real but weak signal: aggregate score rose 4.00 percentage points (4x relative), while certification remained unchanged. This is below the frozen promotion threshold, so eval-time recurrence is not promoted as a law. It does, however, separate E0001's training-budget rival: extra evaluation depth can change behavior without sacrificing training throughput. The remaining residual is representation drift/applicability across repeated steps.

## E0003 context-reinjected eval recurrence
Observation: E0002 improved aggregate score without certifying a rung. Repeated application may be partially useful but progressively lose the original problem context encoded by the prompt.
Hypothesis: the recurrent state needs persistent access to the immutable problem description. Re-injecting the original token+position representation before each extra evaluation-time recurrent step should preserve applicability and improve continuation beyond E0002.
Rival: E0002's 5.33% gain is incidental/nonmechanistic, or the block is not a transition operator; context reinjection will not materially improve certification or score.
Intervention: training remains exactly E0000 (one block application). Evaluation remains four applications as in E0002, but before each of the three extra applications add the original encoded prompt x0 back into the recurrent hidden state. No new parameters, optimizer changes, losses, schedules, or data changes.
Prospective prediction: on Easy E1, E0003 should exceed E0002's 5.33% aggregate score and ideally certify the first T rung.
Kill criterion: no certified-depth gain and aggregate score <=5.33%.
Promotion criterion: any certified Max T gain; otherwise aggregate score >=10% on E1 only licenses a second Easy-world replication, not Medium or Hard.
Hosted H100 Easy E1 result: score 0.33%; Max T none certified; OOD N Max T none certified.
Decision: killed. Naive additive context reinjection destroys the E0002 gain and performs below the frozen baseline. This is evidence against mixing immutable problem context directly into the evolving recurrent state at every step.

## E0004 immutable-context / mutable-state anchored recurrence
Observation: E0002 says extra evaluation-time computation can help, while E0003 says additive re-injection of the prompt corrupts that gain. The unresolved distinction is whether context must remain structurally separate from mutable state rather than being repeatedly merged into it.
Hypothesis: recurrent continuation benefits when the evolving query/state stream is updated against keys/values anchored to the original immutable prompt representation. This preserves applicability information without overwriting the mutable state.
Rival: E0002's gain is incidental, and separating context from state will not improve score or certification.
Intervention: training is exactly the E0000 baseline forward path and optimizer. Evaluation performs the normal first baseline block application, then three extra tied updates in which queries come from the evolving state while keys/values come from the unchanged original token+position context. The same Block parameters are reused; no parameters, optimizer, loss, schedule, or data are added.
Prospective prediction: on Easy E1, E0004 should recover E0002's gain and exceed 5.33% aggregate score; a certified first T rung is the decisive target.
Kill criterion: no certified-depth gain and aggregate score <=5.33%.
Promotion criterion: any certified Max T gain licenses immediate replication on a second Easy world; otherwise aggregate score >=10% licenses that replication but does not yet license Medium or Hard.
Hosted H100 Easy E1 result: score 8.00%; Max T none certified; OOD N Max T none certified.
Decision: RETAIN but do not promote. E0004 beats E0002 by 2.67 percentage points and baseline by 6.67 points, so structural context/state separation improved the same public world. But it missed the frozen >=10% replication threshold and still certified no rung. The next experiment must therefore test a stronger representation change rather than promoting or spending Medium/Hard budget.

## E0005 explicit latent workspace state
Observation: E0004 improved score while keeping immutable context separate, but its mutable state is still the entire token sequence. That may preserve too much representational entanglement: the object being iterated is not a compact computational state but the whole language representation.
Hypothesis: a small explicit mutable workspace, updated against immutable prompt context with tied weights, is a better carrier of serial computation than recurrently rewriting the entire token stream. Training one cheap workspace update should teach the state mechanism without the 4x training-throughput penalty; evaluation can then reuse the same workspace transition four times.
Rival: E0004's improvement does not come from state/context separation, or a one-token workspace is too compressed to carry the necessary computation; score will fail to beat E0004 and certification will remain absent.
Intervention: keep the baseline token encoder/block/head and AdamW. Add no new trainable parameters. Derive one latent workspace token from the encoded prompt, update that workspace by cross-attending to immutable prompt context with the same Block weights, and condition the output token stream on the workspace. Use one workspace update during training and four tied workspace updates during evaluation. The full token stream itself is not recurrently rewritten.
Prospective prediction: on Easy E1, E0005 should exceed E0004's 8.00% aggregate score; decisive evidence is certification of T=1. A score >=10% without certification licenses one second-Easy replication, not Medium or Hard.
Kill criterion: no certified-depth gain and aggregate score <=8.00%.
Promotion criterion: any certified Max T gain, or >=10% aggregate followed by successful replication on a second Easy world.
Hosted H100 Easy E1 result: score 8.33%; Max T none certified; OOD N Max T none certified.
Decision: RETAIN as a weak representation signal but do not promote. The explicit workspace narrowly beats E0004 by 0.33 percentage points, so it passes the literal kill threshold but misses the >=10% replication gate and still certifies no rung. This is not sufficient evidence to enlarge workspace capacity yet because a simpler rival remains: the workspace transition is trained for only one step but evaluated for four, so it may never learn stability under its own recurrent state.

## E0006 two-step workspace training closure test
Observation: E0005 creates a distinct mutable workspace and improves slightly, but the learned transition sees only the initial workspace during training. At evaluation, steps 2-4 receive states produced by the transition itself. That train/eval state-distribution mismatch is a simpler explanation than insufficient workspace capacity.
Hypothesis: exposing the same tied workspace transition to one self-generated recurrent state during training will improve stability and continuation enough to beat E0005, without paying the full four-step training cost that made E0001 uninformative.
Rival: the workspace representation/transition is not genuinely reusable; a second training step only reduces update throughput or compounds drift and will not improve certification or score.
Intervention: exact E0005 architecture, parameters, optimizer, loss, workspace initialization, four-step evaluation and data. Change only training workspace updates from one to two tied applications of the same transition. No new parameters or representation capacity are added.
Prospective prediction: on Easy E1, E0006 should exceed E0005's 8.33% aggregate score; decisive evidence is certification of T=1. A score >=10% without certification licenses a second-Easy replication, not Medium or Hard.
Kill criterion: no certified-depth gain and aggregate score <=8.33%.
Promotion criterion: any certified Max T gain, or >=10% aggregate followed by successful replication on a second Easy world.
Hosted H100 Easy E1 result: score 4.67%; Max T none certified; OOD N Max T none certified.
Decision: KILLED. A second recurrent workspace step during training materially worsened score from 8.33% to 4.67% and did not certify a rung. The simple train/eval recurrent-state exposure explanation is therefore not supported.

## H0001 decisive private Hard test — explicit user-authorized holdout spend
Rationale: the only result that changes the external claim is whether a frozen candidate survives the independently hosted private Hard evaluator. Continued Easy optimization can improve a proxy without answering that question. The user explicitly authorized spending the protected Hard attempt now.
Candidate selection: freeze E0005 exactly as already evaluated. It is the best Easy E1 score in the causal sequence (8.33%) and embodies the most general discovered structural distinction: immutable problem context separated from a compact mutable state. No Hard-specific changes, no Medium tuning, no additional architecture search, and no hidden-evaluator feedback are incorporated before submission.
Prospective prediction: the decisive positive outcome is any certified Hard Max T >= 1. A stronger outcome also certifies OOD N Max T >= 1. A successful Hard run with both certified depths still below 1 is a falsification of the current transfer claim, even if its first-rung accuracy is nonzero.
Interpretation table:
- Hard Max T >= 1: external capability breakthrough; freeze immediately and run source-distinct/ablation analysis before further tuning.
- Hard Max T < 1 but OOD N Max T >= 1: unusual scope split; do not call a general breakthrough; investigate applicability only after preserving the result.
- Both < 1: current Easy gains did not cross the private capability boundary. Treat as a protected negative, not as permission to tune against private details.
- Evaluation failure/timeout/OOM: infrastructure/resource residual only; no semantic conclusion.
Trust boundary: Hard is private, hosted, and automatically leaderboard-affecting. This submission consumes the one accepted Hard attempt for the UTC day. From this point onward Hard is no longer an untouched holdout for this candidate lineage.
