# V158 Experiential Map Rescue — 2026-08-18

Status: PASS.

Workflow run: 32058878246
Artifact: v158-experiential-map-rescue
Artifact SHA256: 3cf158ab76303feb72657c908be67eeac1864de96f220da3b9d8014f4460bb51
Protocol frozen before outcomes in results/V158_PROTOCOL_FROZEN_20260818.md.

No weight updates. For each lineage, the controller inferred its state map only from two prior verified calibration examples containing A, AB, and ABC outputs. It inferred the AB extension and ABC wrapper boundaries, froze that map, and then controlled eight held-out inputs at the V155 step-2 first-loss checkpoint. Held-out target answers were used only by the verifier after control. Causal ablation used the next lineage's verified experience to infer a wrong but structurally valid map.

## Learned maps
- seed 20260821: suffix `-zu`, wrapper `[` `]`
- seed 20260822: suffix `-xx`, wrapper `{` `}`
- seed 20260823: suffix `-ri`, wrapper `(` `)`

## Step-2 exact hits (of 8)

### Seed 20260821
- A: raw 0 -> experiential map 6; shuffled-experience ablation 0
- AB: raw 0 -> experiential map 2; ablation 0
- ABC: raw 6 -> 6; ablation 6

### Seed 20260822
- A: raw 0 -> experiential map 8; ablation 0
- AB: raw 0 -> experiential map 8; ablation 0
- ABC: raw 5 -> 5; ablation 5

### Seed 20260823
- A: raw 2 -> experiential map 7; ablation 2
- AB: raw 1 -> experiential map 6; ablation 1
- ABC: raw 7 -> 7; ablation 7

## Aggregate
- A: raw 2/24 -> experiential map 21/24; shuffled-experience ablation 2/24
- AB: raw 1/24 -> experiential map 16/24; shuffled-experience ablation 1/24
- ABC: 18/24 unchanged.

Correct prior verified experience therefore produced +19 A recoveries and +15 AB recoveries under identical frozen neural weights. Shuffled verified experience produced zero gain. The controller did not know held-out answers and did not receive hard-coded structural constants; it inferred them from prior verified experience.

## Claim boundary
This is a minimal synthetic demonstration of verified experiential state causally preserving access to earlier capabilities under neural interference. It does not establish broad real-world VDI. The next high-value move is external-domain transfer: repeat the same architecture where the state map must be learned from real verifier outcomes rather than a synthetic string grammar.
