# MIDDLE_DIGIT_ALGEBRA_MAP_V1

Three-seed residual remap after the carry-causal suite failed promotion. Same 30% support and 500-step budget; stable-width squaring only.

## Model summary

- seed 0: exact=0.0108, final_loss=0.4313
- seed 1: exact=0.0114, final_loss=0.4079
- seed 2: exact=0.0078, final_loss=0.4298

## Strongest one-factor algebraic separators

| rank | feature | threshold | mean accuracy effect (high-low) | seed effects |
|---:|---|---:|---:|---|
| 1 | edge_distance | 1 | -0.710 | -0.717,-0.703,-0.711 |
| 2 | n_terms | 2 | -0.643 | -0.640,-0.645,-0.644 |
| 3 | edge_distance | 2 | -0.619 | -0.615,-0.622,-0.620 |
| 4 | n_terms | 1 | -0.602 | -0.604,-0.607,-0.596 |
| 5 | n_terms | 3 | -0.534 | -0.534,-0.536,-0.533 |
| 6 | carry_in | 0 | -0.527 | -0.533,-0.519,-0.528 |
| 7 | carry_in | 9 | -0.525 | -0.525,-0.538,-0.513 |
| 8 | edge_distance | 0 | -0.525 | -0.528,-0.528,-0.520 |
| 9 | carry_in | 8 | -0.525 | -0.516,-0.548,-0.510 |
| 10 | carry_in | 11 | -0.508 | -0.504,-0.530,-0.489 |

## Position gap

- seed 0 d=3: edge=1.000, middle=0.470, middle-edge=-0.530
- seed 0 d=4: edge=1.000, middle=0.472, middle-edge=-0.528
- seed 1 d=3: edge=1.000, middle=0.475, middle-edge=-0.525
- seed 1 d=4: edge=1.000, middle=0.471, middle-edge=-0.529
- seed 2 d=3: edge=1.000, middle=0.464, middle-edge=-0.536
- seed 2 d=4: edge=1.000, middle=0.481, middle-edge=-0.519

## Decision

Top landmark: **edge_distance @ 1**, mean effect -0.710, same-direction across seeds=True.
This clears the rapid landmark threshold for a targeted causal separator; do not yet call it an obstruction until intervention/ablation.

## Claim boundary

Diagnostic CPU map only; this localizes digit-level squaring residuals and makes no leaderboard or modular-squaring claim.