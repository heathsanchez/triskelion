# CARRY_CAUSAL_SUITE_V1

Frozen 3-seed causal suite after SQUARE_EXACTNESS_CARTOGRAPHY_V1. Coverage=30%, 450 steps, stable-width only, identical support/eval sets across arms.

## Precommitted decisions

- Promote carry obstruction if baseline low→high exact drop is >=15pp on mean and negative in all 3 seeds for either digit length.
- Promote LSB-first repair if high-carry exact gain vs baseline is >=15pp mean while low-carry control moves <10pp absolute.
- Promote recurrent propagation repair under the same rule.
- Otherwise retain carry as a landmark but do not claim causal repair.

| digits | arm | low exact mean | high exact mean | carry drop |
|---:|---|---:|---:|---:|
| 3 | baseline_msd | 0.085 | 0.024 | -0.062 |
| 3 | lsd_first | 0.085 | 0.024 | -0.062 |
| 3 | recurrent_msd | 0.128 | 0.027 | -0.102 |
| 4 | baseline_msd | 0.086 | 0.002 | -0.084 |
| 4 | lsd_first | 0.086 | 0.002 | -0.084 |
| 4 | recurrent_msd | 0.089 | 0.004 | -0.085 |

## Intervention effects

- d=3 **lsd_first**: high-carry rescue=+0.000 seeds=[0.0, 0.0, 0.0]; low-control move=+0.000 seeds=[0.0, 0.0, 0.0]
- d=3 **recurrent_msd**: high-carry rescue=+0.003 seeds=[0.0, -0.009, 0.018]; low-control move=+0.043 seeds=[0.128, 0.0, 0.0]
- d=4 **lsd_first**: high-carry rescue=+0.000 seeds=[0.0, 0.0, 0.0]; low-control move=+0.000 seeds=[0.0, 0.0, 0.0]
- d=4 **recurrent_msd**: high-carry rescue=+0.003 seeds=[0.005, -0.003, 0.005]; low-control move=+0.003 seeds=[0.009, 0.009, -0.009]

## Decision

Promoted under frozen rules: **none**

## Claim boundary

CPU causal separator on squaring only; no leaderboard or modular-squaring claim. LSB-first is a representation probe; recurrent_msd is an architecture probe.