# REDUCTION_WIDTH_QUOTIENT_SEPARATOR_V3 — prospective protocol

**Status:** `FROZEN_BEFORE_V3_OUTCOME`

## Residual from V2

V2 held support density (~50%) and random-sampling exposure (20 epochs) constant. It produced a material fresh digit-excess drop between `N=143` and `N=377`, and the highest normalized quotient quartile at `N=377` was the weakest internal stratum.

However, V2 crossed two boundaries together:

1. quotient/modulus scale increased substantially;
2. `N^2` crossed `100,000`, so the varying reduction input `y` acquired a sixth decimal digit.

V3 is the minimal contrast separating these explanations before any representation or architecture intervention.

## Frozen fixed moduli

Use the exact reduction task `y -> y mod N` and the unchanged public One Layer Deeper tokenizer/model harness.

Four fixed semiprimes straddle the decimal input-width boundary while keeping `N` itself three digits and allowing three-digit quotients:

- `N=247 = 13*19`, `N^2=61,009` — max `y` width 5
- `N=299 = 13*23`, `N^2=89,401` — max `y` width 5
- `N=323 = 17*19`, `N^2=104,329` — max `y` width 6
- `N=377 = 13*29`, `N^2=142,129` — max `y` width 6

This creates the nearest practical semiprime contrast around `sqrt(100000) ≈ 316.2`.

## Frozen training/evaluation controls

- model seed `0`
- data seed `45`
- `L2 d128`, 2 heads
- batch `256`
- coverage `0.50`
- random-sampling exposure `20` effective epochs
- `n_train=floor(0.5*N^2)`
- `steps=ceil(20*n_train/256)`
- fresh `n_eval=2000` where legal
- AdamW/lr/warmup/clip unchanged from V2/harness
- CPU explicitly selected

Per-example output records the same V2 fields, plus a Boolean `y_six_digits`.

## Frozen decision rule

Primary contrast is `N=299` versus `N=323`.

- **INPUT_WIDTH_BOUNDARY** if `N=299` remains strongly above chance but `N=323` suffers a material fresh digit-excess drop of at least `0.10`.
- **QUOTIENT_SCALE_BOUNDARY** if performance is already materially degraded at `N=299` relative to the V2 `N=143` anchor, with no additional >=0.10 discontinuity at `299 -> 323`.
- **COMBINED_BOUNDARY** if `N=299` is degraded and `299 -> 323` also drops >=0.10.
- **NO_MATERIAL_BOUNDARY_IN_THIS_WINDOW** if neither contrast reaches 0.10.

Secondary localization compares normalized quotient quartiles within each fixed modulus. These strata may identify a local quotient threshold but may not override the frozen primary contrast.

V2 `N=143` digit excess `+0.20471` is frozen as the lower-scale anchor for the push-run artifact already recorded on this branch.

## Claim boundary

This is a minimal behavioral separator inside the same decimal representation and small encoder. It distinguishes scale from the five-to-six-digit input-format transition in this bounded world; it does not establish universal arithmetic difficulty.
