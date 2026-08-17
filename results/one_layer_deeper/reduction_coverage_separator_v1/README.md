# REDUCTION_COVERAGE_SEPARATOR_V1

Tests whether the apparent reduction wall was merely a training-coverage artifact.

| task | bits | coverage | cohort | exact | chance | excess | digit | digit chance |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| square | 14 | 41.336% | train_seen | 0.00400 | 0.00200 | +0.00200 | 0.54529 | 0.18551 |
| square | 14 | 41.336% | test_fresh | 0.00200 | 0.00200 | +0.00000 | 0.53706 | 0.18056 |
| reduce | 7 | 60.379% | train_seen | 0.12400 | 0.02200 | +0.10200 | 0.47441 | 0.13539 |
| reduce | 7 | 60.379% | test_fresh | 0.07200 | 0.02200 | +0.05000 | 0.42827 | 0.13390 |
| squaremod | 14 | 41.336% | train_seen | 0.00000 | 0.00600 | -0.00600 | 0.15792 | 0.17558 |
| squaremod | 14 | 41.336% | test_fresh | 0.00200 | 0.00600 | -0.00400 | 0.15900 | 0.17221 |

## Separator readout

- square: coverage=41.336%, exact_excess=+0.00000, digit_excess=+0.35650
- reduce: coverage=60.379%, exact_excess=+0.05000, digit_excess=+0.29437
- squaremod: coverage=41.336%, exact_excess=-0.00400, digit_excess=-0.01321

**Coverage rival survives / reduction becomes learnable at matched coverage.** The previous reduction wall was at least partly a data-support artifact; next map must hold coverage constant while increasing quotient/reduction complexity.

## Claim boundary

Cheap matched CPU diagnostic only. Different modulus bit-widths are intentionally used to equalize input-space coverage, so this localizes the support-vs-operation rival but is not a competition-performance comparison.