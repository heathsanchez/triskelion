# V156 First-Loss Control Rescue — 2026-08-18

Status: PASS — frozen-protocol run completed successfully with no weight updates.

Workflow run: 32058108874
Artifact: v156-first-loss-control-rescue
Artifact SHA256: 4ed4d11e30548a932a981cbba4b4dfed2db2eb4efa9d2b05ed71f15743857f1e
Frozen protocol: results/V156_PROTOCOL_FROZEN_20260818.md, committed before run 2.

## Step-2 first-loss checkpoint results (exact hits of 8)

### Seed 20260821
- A: raw 0; termination-only 0; state-projection 6
- AB: raw 0; termination-only 0; state-projection 2
- ABC: raw 6

### Seed 20260822
- A: raw 0; termination-only 0; state-projection 8
- AB: raw 0; termination-only 0; state-projection 8
- ABC: raw 5

### Seed 20260823
- A: raw 2; termination-only 2; state-projection 8
- AB: raw 1; termination-only 1; state-projection 6
- ABC: raw 7

Aggregate step-2:
- A raw 2/24 -> projection 22/24
- AB raw 1/24 -> projection 16/24
- ABC raw 18/24

Termination-only did not rescue the collapsed step-2 cases, so the dominant failure is not merely failure to emit EOS after an otherwise-correct prefix.

State projection did rescue a large fraction under identical frozen weights. In the cleanest replicate (seed 20260822), Task A and Task AB both emitted the full ABC-shaped trajectory `{pv-<x>-xx}` for all eight held-out inputs. The exact A state `pv-<x>` and exact AB state `pv-<x>-xx` were therefore already present contiguously inside the emitted trajectory even though direct task accuracy was 0/8 for both. Selecting the corresponding internal state restored A=8/8 and AB=8/8 without altering weights.

## Claim boundary
This does not yet prove a practical learned router, because the V156 projection test checks for the known exact target string before selecting it. It does show that direct failure can coexist with literal emission of the earlier correct state inside a longer trajectory. That falsifies a simple content-deletion interpretation for those rescued cases.

The next stricter separator is answer-blind structural projection: the controller may know only the learned state grammar/boundaries (e.g. remove outer wrapper for AB; remove outer wrapper and terminal suffix for A) and may not search for, construct, or compare against the target answer during control. Protected targets are used only by the verifier after projection.
