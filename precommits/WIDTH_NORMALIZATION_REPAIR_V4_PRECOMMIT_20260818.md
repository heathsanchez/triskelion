# WIDTH_NORMALIZATION_REPAIR_V4 — prospective precommit

Date: 2026-08-18

## Question

Does the previously localized 5-digit -> 6-digit input-width boundary cause a material part of the capability collapse at fixed modular-reduction semantics, such that changing only the width representation restores capability?

This test is a prospective follow-up to `REDUCTION_WIDTH_QUOTIENT_SEPARATOR_V3`, which found a frozen verdict `INPUT_WIDTH_BOUNDARY` with a large drop in digit-excess from N=299 to N=323 while matched support coverage remained ~50%.

## Frozen external substrate

Repository: `benjaminW2025/one-layer-deeper`
Commit: `697a78d4be579745f3b410c01c966c91e7094ad4`

The checkout MUST succeed exactly at that SHA. No `|| true`, fallback branch, or moving default branch is permitted.

## Semantics

For each fixed modulus N in {299, 323, 377}, sample the same deterministic 50% training support and 2,000 held-out examples using the V3 data protocol. The target remains exactly `r = y mod N` with t=1. No labels, examples, support density, optimizer budget, model architecture, model seed, or evaluation metric may change across representation arms.

## Representation arms

A. `ORIGINAL`: upstream decimal tokenization.

B. `PAD_X6`: identical upstream tokenization except the X/y field is left-zero-padded to exactly 6 decimal digit tokens before T. N, T, output/result tokenization, vocabulary, labels, and semantics are unchanged. Existing digit token 0 is used; no new token or side channel is introduced.

This intervention changes only the representation of X/y width.

## Model / training

Same as V3:
- EncoderModel
- d_model=128
- n_layers=2
- n_heads=2
- CPU
- model seed=0
- data seed=45
- epochs=20
- batch=256
- AdamW lr=3e-4, weight_decay=0.01
- warmup=50
- grad clip=1.0

## Primary quantities

For each N and arm record:
- digit accuracy
- exact accuracy
- corresponding chance baselines
- digit excess = digit accuracy - chance digit
- exact excess
- first/final loss and divergence/flat flags

Let `E_A(N)` be ORIGINAL digit excess and `E_B(N)` be PAD_X6 digit excess.

## Frozen gates

G0 REPRODUCE_BOUNDARY: `E_A(299) - E_A(323) >= 0.15`.

G1 N323_REPAIR: `E_B(323) - E_A(323) >= 0.10`.

G2 N323_RESTORE_LEVEL: `E_B(323) >= 0.75 * E_A(299)`.

G3 N377_REPAIR: `E_B(377) - E_A(377) >= 0.08`.

G4 CONTROL_NOT_GLOBAL_MAGIC: improvement at N323 must exceed improvement at N299 by at least 0.05: `(E_B(323)-E_A(323)) - (E_B(299)-E_A(299)) >= 0.05`.

G5 TRAINING_VALID: all six cells are non-divergent and not flat-from-start under the frozen loss criterion.

### Scientific verdicts

- `PASS_WIDTH_REPRESENTATION_REPAIR` iff G0..G5 all pass.
- `PARTIAL_WIDTH_REPRESENTATION_REPAIR` iff G0, G1, and G5 pass but one or more of G2/G3/G4 fail.
- `NO_WIDTH_REPRESENTATION_REPAIR` iff G0 and G5 pass but G1 fails.
- `NULL_BOUNDARY_NOT_REPRODUCED` iff G0 fails or required cells are invalid.

No threshold may be changed after execution.

## Causal interpretation / ablation

`ORIGINAL -> PAD_X6` is the representation intervention. Re-running the matched ORIGINAL arm is the precommitted ablation/control. This experiment does not claim inference-time toggling of a fixed trained model; it tests whether matched neural capability depends causally on the chosen input representation under identical semantics and training budget.

## Claim boundary

A PASS would support: in this pinned neural program-learning setting, a verifier-localized input-width residual identifies a causal representation defect, and canonicalizing only that width materially restores capability under matched semantics and budget.

It would NOT establish general developmental intelligence, open-ended representation invention, autonomous diagnosis, or universal arithmetic behavior. Those require separate tests.
