# EXPLICIT_STAGING_SEPARATOR_V1

Tests whether exposing the intermediate y=x^2 rescues modular reduction relative to direct x->x^2 mod N learning.

| bits | N | square exact | oracle y→reduce exact | learned square→reduce chain | direct squaremod exact | reduce support |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 143 | 0.000 | 0.033 | 0.000 | 0.033 | 24.5% |
| 10 | 899 | 0.020 | 0.010 | 0.010 | 0.010 | 0.6% |

## Decision

**No robust explicit-intermediate rescue:** composition/interface is not yet isolated; inspect primitive exactness and scale effects before intervention.

## Claim boundary

Oracle-stage performance asks whether reduction can act when the intermediate is represented explicitly and correctly. Learned-chain performance additionally requires exact square predictions, so it is bounded by square-stage errors. This is a rapid CPU separator, not a leaderboard result.