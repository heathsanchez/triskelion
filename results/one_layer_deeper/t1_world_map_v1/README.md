# T1_WORLD_MAP_V1

Forest-first cartography for One Layer Deeper using public executed evidence.

- Source rows: **150**
- T=1 rows: **12**
- Earliest visible boundary: **FRESH_X_BASE_OPERATION**
- Mean T=1 seen-N exact excess over chance: **-0.026043666666666666**
- Mean T=1 OOD-N exact excess over chance: **-0.013023333333333333**
- Steps/generalization Pearson: **-0.1968512879934575**

## Ranked behavioral classes

| regime | budget | ood_n | exact | chance | excess | digit excess | runs |
|---|---:|:---:|---:|---:|---:|---:|---:|
| easy_sampled_b1011 | steps=1500.0 | True | 0.00521 | 0.01562 | -0.01042 | -0.02991 | 3 |
| easy_sampled_b1011 | seconds=60.0 | True | 0.00000 | 0.01562 | -0.01562 | -0.04060 | 1 |
| easy_sampled_b1011 | seconds=60.0 | False | 0.00781 | 0.02344 | -0.01563 | -0.07291 | 1 |
| easy_sampled_b1011 | steps=1500.0 | False | 0.00781 | 0.02344 | -0.01563 | -0.04861 | 3 |
| e1_fixed323 | seconds=60.0 | True | 0.01562 | 0.03125 | -0.01563 | -0.09948 | 1 |
| e1_fixed323 | steps=1500.0 | True | 0.01562 | 0.03125 | -0.01563 | -0.09424 | 1 |
| e1_fixed323 | seconds=60.0 | False | 0.00000 | 0.04688 | -0.04688 | -0.10796 | 1 |
| e1_fixed323 | steps=1500.0 | False | 0.00000 | 0.04688 | -0.04688 | -0.11364 | 1 |

## Missing coordinates for the real per-example map

- per-example x and N
- digit width of x and N
- whether x^2 < N (no modular reduction needed)
- quotient floor(x^2/N) / reduction complexity
- multiplication carry count
- longest carry chain
- answer width
- per-place prediction correctness
- positional alignment / field offsets
- same-example outcomes across competing representations

## Claim boundary

V1 maps only cohort-aggregate public evidence. It can locate broad upstream capability boundaries but cannot attribute failure to carry, reduction, or place-value without per-example predictions.

## Next deciding test

Run one trained model over a stratified per-example T=1 diagnostic population and join predictions to arithmetic descriptors; mine minimal success/failure contrasts before any architecture change.
