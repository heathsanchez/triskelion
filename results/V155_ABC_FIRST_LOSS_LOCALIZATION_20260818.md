# V155 ABC First-Loss Localization — 2026-08-18

## Status
PASS — external River rerun completed successfully from the exact successful V10 AB checkpoints.

Workflow run: 32056410501
Artifact: v155-abc-first-loss-localization
Artifact SHA256: 2edd1531f54b8cd1ad4e325bc65913beeea64ff43b0f865d8c3abc378d377eeb

Protocol: restart from the exact successful V10 AB checkpoint for each of three independent seeds, replay the original frozen ABC batch and optimizer settings, save and probe every ABC update, no adaptive stopping.

## Stepwise direct exact hits (of 8 held-out strings)

### Seed 20260821
- step 0: A 8, AB 8, ABC 0
- step 1: A 8, AB 7, ABC 0
- step 2: A 0, AB 0, ABC 6
- step 3: A 0, AB 0, ABC 8
- step 4: A 8, AB 5, ABC 8
- step 5: A 0, AB 0, ABC 8
- step 6: A 8, AB 8, ABC 8
First A loss: step 2. First AB loss: step 1.

### Seed 20260822
- step 0: A 8, AB 8, ABC 0
- step 1: A 6, AB 8, ABC 0
- step 2: A 0, AB 0, ABC 5
- step 3: A 0, AB 0, ABC 8
- step 4: A 6, AB 8, ABC 2
- step 5: A 8, AB 8, ABC 8
- step 6: A 8, AB 8, ABC 8
First A loss: step 1. First AB loss: step 2.

### Seed 20260823
- step 0: A 8, AB 6, ABC 0
- step 1: A 8, AB 0, ABC 0
- step 2: A 2, AB 1, ABC 7
- step 3: A 1, AB 3, ABC 6
- step 4: A 5, AB 8, ABC 0
- step 5: A 4, AB 4, ABC 7
- step 6: A 7, AB 6, ABC 8
First A loss: step 2. First AB loss: step 1.

## Prefix-continuation findings
AB-seed -> ABC closing transition was 0/8 at every tested step for all three seeds. A-seed -> AB and wrapped-A continuation were variable across seeds and steps rather than monotonically lost.

## Interpretation boundary
The experiment does not support a simple permanent-forgetting account. Direct A/AB competence can disappear abruptly after one or two ABC updates and later reappear under the same frozen replay/consolidation process. The observed dynamics are oscillatory and seed-dependent, consistent with interference in activation/termination/control boundaries rather than irreversible deletion of the underlying operator alone.

The strongest next separator is token-level/state-level control analysis around the first-loss transition (step 1->2), comparing output-token likelihood/termination behavior and testing whether an external state/stop controller can stabilize A/AB while preserving ABC.
