# V157 Answer-Blind Structural Rescue — 2026-08-18

Status: PASS.

Workflow run: 32058558236
Artifact: v157-answer-blind-structural-rescue
Artifact SHA256: 3170bb30b92c1f5a92969f28349dc8e3ffa2cdfc2fa41c6541e1318c338fc936
Protocol was frozen before outcomes in results/V157_PROTOCOL_FROZEN_20260818.md.

No weight updates. The controller never computed, searched for, compared against, or constructed the protected target during control. It used only the lineage structural grammar: wrapper boundaries and suffix boundary. Protected targets were used only by the verifier after control output was frozen.

## Step-2 exact hits (of 8)

### Seed 20260821
- A: raw 0 -> correct structural controller 6; permuted-grammar ablation 0
- AB: raw 0 -> controller 2; ablation 0
- ABC: raw 6 -> controller 6; ablation 6

### Seed 20260822
- A: raw 0 -> controller 8; ablation 0
- AB: raw 0 -> controller 8; ablation 0
- ABC: raw 5 -> controller 5; ablation 5

### Seed 20260823
- A: raw 2 -> controller 7; ablation 2
- AB: raw 1 -> controller 6; ablation 1
- ABC: raw 7 -> controller 7; ablation 7

## Aggregate
- A: raw 2/24 -> controller 21/24; wrong-grammar ablation 2/24
- AB: raw 1/24 -> controller 16/24; wrong-grammar ablation 1/24
- ABC: 18/24 unchanged by either controller.

The correct structural controller therefore produced +19 A recoveries and +15 AB recoveries under identical frozen weights, while the permuted structural grammar produced zero gain. ABC was not degraded.

## Interpretation
This is stronger than V156 because rescue does not depend on knowing the protected answer string. At the first-loss boundary, a small answer-blind controller that knows the correct developmental state boundaries can recover earlier capabilities that direct model control no longer selects. The causal ablation shows the gain depends on the correct learned boundary structure, not generic post-processing capacity.

Claim boundary: the structural grammar is still supplied explicitly from the synthetic task specification. The next separator must infer that grammar from prior verified developmental experience and apply it to held-out inputs without hand-coded transformation constants. If that transfers, the result becomes a direct minimal demonstration of verified experiential state preserving capability under neural interference.
