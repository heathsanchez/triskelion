# WIDTH_POSITION_MECHANISM_V5 — prospective fast mechanism discriminator

Date: 2026-08-18
Status: `FROZEN_BEFORE_V5_OUTCOME`

## Why this test exists

`WIDTH_NORMALIZATION_REPAIR_V4` returned the preregistered verdict `NO_WIDTH_REPRESENTATION_REPAIR`.

The decisive pattern was not a uniform padding benefit:

- N=323: PAD_X6 minus ORIGINAL digit-excess = -0.00910;
- N=377: PAD_X6 minus ORIGINAL digit-excess = +0.23470;
- N=299 control: PAD_X6 minus ORIGINAL digit-excess = -0.26980.

Therefore V4 falsified the simple claim that the N=299 -> N=323 discontinuity is repaired by canonical six-digit zero padding. This V5 test MUST NOT overturn, relabel, or rescue that verdict.

The remaining decision-changing question is narrower: why did the same intervention materially help N=377 but not N=323? One plausible mechanism is positional geometry. In the upstream representation, the X width changes the absolute positions of T and of the logits used for the result. PAD_X6 simultaneously (a) right-aligns X digits, (b) fixes T/result positions, and (c) inserts literal zero digit tokens. V4 did not separate those effects.

## Frozen external substrate

Repository: `benjaminW2025/one-layer-deeper`
Commit: `697a78d4be579745f3b410c01c966c91e7094ad4`

Checkout MUST succeed exactly at this SHA. No fallback, moving default branch, or `|| true` is allowed.

## Frozen semantic cells

Only the two V4 diagnostic cells are run:

- N=323 = 17*19
- N=377 = 13*29

For each N use the same deterministic V3/V4 support construction:

- data RNG `random.Random(45 + N)`;
- 50% of the complete N^2 support for training;
- 2,000 held-out examples;
- target exactly `r = y mod N`, with t=1.

Within each N every arm receives exactly the same train and held-out y values and labels.

## Frozen representation arms

All arms use `MAX_SEQ_LEN=13`, the same vocabulary, labels, model parameterization, optimizer, seed, and training budget.

A. `ORIGINAL`

The pinned upstream decimal tokenizer with ordinary variable-width X/y. All prompt tokens are attended.

B. `PAD_X6`

The V4 intervention: X/y is left-zero-padded to six decimal digit tokens. This jointly right-aligns the meaningful X digits, fixes T/result positions, and exposes literal zero tokens.

C. `X_ALIGN_MASK6`

Reserve a six-slot X field, right-align the ordinary X digits, and fill unused leading X slots with the existing PAD token with attention mask false. T/result positions therefore match PAD_X6, and meaningful X digits occupy the same absolute positions as PAD_X6, but no literal leading-zero digit content is visible to attention.

D. `T_ALIGN_MASK6`

Keep ordinary X digits in the same left-aligned positions as ORIGINAL, then insert attention-masked PAD slots after X until the X field occupies six slots. This fixes T/result positions without right-aligning the meaningful X digits and without visible leading-zero content.

Thus the contrasts are:

- PAD_X6 vs ORIGINAL = X alignment + T/result alignment + zero-token content;
- X_ALIGN_MASK6 vs ORIGINAL = X alignment + T/result alignment, without zero-token content;
- T_ALIGN_MASK6 vs ORIGINAL = T/result alignment only, without X right-alignment or zero-token content.

## Frozen fast training budget

This is a mechanism screen, not a restoration claim.

- EncoderModel
- d_model=128
- n_layers=2
- n_heads=2
- CPU
- model seed=0
- data seed=45+N as above
- epochs=6
- batch=256
- AdamW lr=3e-4, weight_decay=0.01
- warmup=50
- grad clip=1.0

No epoch escalation is permitted after outcome inspection. If the six-epoch PAD signature does not reproduce, the result is a null fast screen.

## Primary quantity

For each N and arm record digit accuracy, exact accuracy, chance baselines, digit/exact excess, losses, steps, and training validity.

Let E(N,A) be digit excess and I(N,A)=E(N,A)-E(N,ORIGINAL).

## Frozen eligibility gates

E0 `TRAINING_VALID`: all eight cells are non-divergent and not flat-from-start.

E1 `PAD_SIGNATURE_REPRODUCED`: I(377,PAD_X6) >= 0.06.

E2 `PAD_377_SPECIFIC`: I(377,PAD_X6) - I(323,PAD_X6) >= 0.06.

If E0..E2 do not all pass, verdict is `NULL_FAST_SCREEN_V4_SIGNATURE_NOT_REPRODUCED`. No mechanism conclusion is allowed.

## Frozen mechanism classifications

Evaluated only if E0..E2 pass.

`TARGET_POSITION_ALIGNMENT_SUFFICIENT` iff:

- I(377,T_ALIGN_MASK6) >= 0.05;
- I(377,T_ALIGN_MASK6) >= 0.75 * I(377,PAD_X6); and
- I(377,T_ALIGN_MASK6) - I(323,T_ALIGN_MASK6) >= 0.05.

`X_POSITION_ALIGNMENT_SUFFICIENT` iff TARGET_POSITION_ALIGNMENT_SUFFICIENT is false and:

- I(377,X_ALIGN_MASK6) >= 0.05;
- I(377,X_ALIGN_MASK6) >= 0.75 * I(377,PAD_X6); and
- I(377,X_ALIGN_MASK6) - I(323,X_ALIGN_MASK6) >= 0.05.

`LITERAL_ZERO_CONTENT_REQUIRED` iff neither alignment-sufficient verdict holds and both masked-arm effects at N=377 are at most 30% of the reproduced PAD_X6 effect:

- I(377,X_ALIGN_MASK6) <= 0.30 * I(377,PAD_X6); and
- I(377,T_ALIGN_MASK6) <= 0.30 * I(377,PAD_X6).

Otherwise verdict is `MIXED_POSITION_CONTENT_MECHANISM`.

The classification order above is frozen to avoid post-hoc relabeling.

## Controls and non-claims

V4's N=299 matched control already rejects the explanation that literal PAD_X6 simply helps every modulus; V5 does not spend runtime repeating that established control.

V5 does not test a new repair, does not change V4's scientific verdict, and does not claim developmental intelligence. It only discriminates which component of the already-observed N=377 PAD_X6 effect is sufficient under a shorter matched diagnostic budget.

A non-null positional verdict would justify retiring the broad `INPUT_WIDTH_BOUNDARY -> zero-pad` causal story and replacing it with a narrower positional-geometry residual for subsequent replication across fresh moduli. A literal-zero or mixed verdict would require a different fresh-modulus discriminator before any representation-development claim.