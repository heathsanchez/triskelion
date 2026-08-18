# N377_PAD_LEARNING_CURVE_V6 — prospective terminal width-line discriminator

Date: 2026-08-18
Status: `FROZEN_BEFORE_V6_OUTCOME`

## Motivation

V4 established a matched but modulus-specific intervention pattern: PAD_X6 failed to repair N=323 while materially helping N=377 at 20 epochs. Independent automatic V4 executions differed substantially in magnitude but agreed on that gate pattern.

V5 then used a prospectively frozen six-epoch fast screen. Its first automatic execution was ineligible for mechanism classification because the V4 N=377 PAD signature did not reproduce: at six epochs PAD_X6 improved N=377 digit excess by only +0.00240. The V5 null cannot be rescued by increasing V5's frozen budget.

The smallest remaining decision-changing question is temporal: is the V4 N=377 effect a delayed training-dynamics interaction that emerges after the six-epoch screen, or does a new full-budget matched execution fail to reproduce the effect at all?

This V6 is terminal for the arithmetic width line. It does not test another repair. After V6, no same-target representation tuning is permitted as a bridge to the Developmental Intelligence demo.

## Frozen external substrate

Repository: `benjaminW2025/one-layer-deeper`
Commit: `697a78d4be579745f3b410c01c966c91e7094ad4`

Checkout MUST succeed exactly at this SHA. No fallback or moving branch is permitted.

## Frozen semantic cell

Only N=377 = 13*29 is run.

- deterministic support RNG: `random.Random(45 + 377)`;
- 50% of N^2 support for training;
- 2,000 held-out examples;
- target exactly `r = y mod N`, t=1;
- same train and held-out y values for both arms.

## Frozen arms

A. `ORIGINAL`: pinned upstream variable-width decimal X/y representation.

B. `PAD_X6`: V4 left-zero-padding of X/y to exactly six visible decimal digit tokens.

No other representation arm exists in V6.

## Frozen model and optimizer

Exactly the V4 N=377 setup:

- EncoderModel
- max_seq_len=13
- d_model=128
- n_layers=2
- n_heads=2
- model seed=0
- data seed=45+N
- batch=256
- AdamW lr=3e-4, weight_decay=0.01
- warmup=50
- grad clip=1.0
- maximum training horizon=20 epochs
- CPU

Each arm is initialized independently from the same model seed and receives the same sampled minibatch index stream, as in V4.

## Single-training checkpoint protocol

Each arm is trained once to the 20-epoch step budget. Without resetting or modifying the model, held-out metrics are recorded at the first training step at or beyond each frozen epoch-equivalent checkpoint:

`[6, 10, 14, 18, 20]`.

Checkpoint step for epoch e is `ceil(e * n_train / batch)`.

The evaluation set is fixed and evaluation does not update weights or optimizer state.

Record per checkpoint and arm:

- digit accuracy;
- chance digit baseline;
- digit excess;
- exact accuracy and exact excess;
- mean recent training loss;
- elapsed seconds.

Also record Python, PyTorch, platform, CPU/thread metadata so numerical runner variation is visible rather than hidden.

## Frozen primary quantity

Let `I_e = digit_excess(PAD_X6,e) - digit_excess(ORIGINAL,e)`.

The inherited material-effect threshold is +0.08, exactly V4 gate G3.

## Frozen verdict

`NULL_N377_V4_EFFECT_NOT_REPRODUCED` iff `I_20 < 0.08` or either arm is invalid/divergent.

Otherwise V4's N=377 effect is reproduced in this execution and:

- `EARLY_PERSISTENT_PAD_ADVANTAGE` iff `I_6 >= 0.08`;
- `DELAYED_PAD_ADVANTAGE` iff `I_6 < 0.08` and `I_20 >= 0.08`.

For a delayed verdict, record the first frozen checkpoint in `[10,14,18,20]` where `I_e >= 0.08`; do not invent an interpolated crossing time.

No threshold, checkpoint, seed, or budget may change after outcome inspection.

## Interpretation boundary

A delayed verdict supports only: in this pinned N=377 small-encoder setting, the PAD_X6 advantage is a training-dynamics interaction that is absent early and material later under the frozen optimizer trajectory.

It does NOT repair N=323, validate a generic 5-digit -> 6-digit causal boundary, establish a representation-development mechanism, or support Developmental Intelligence.

A null kills the N=377 padding effect as insufficiently reproducible for further mechanistic investment in this line.

Regardless of verdict, this arithmetic line is not the bridge to the real-code twin demo. The next Developmental Intelligence work must return to source-distinct real-code episodes and the already-frozen V145/Lean developmental lineages.