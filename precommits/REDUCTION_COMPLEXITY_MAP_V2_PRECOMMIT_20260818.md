# REDUCTION_COMPLEXITY_MAP_V2 — prospective protocol

**Status:** `FROZEN_BEFORE_V2_OUTCOME`

## Why this is the next deciding test

The previous matched-coverage separator showed that `reduce` becomes learnable at high input-space coverage while `squaremod` still fails, so the earlier reduction wall was at least partly a support-density artifact. The remaining rival is whether reduction difficulty returns as quotient complexity grows even when support density and training exposure are controlled.

This protocol therefore changes **quotient/reduction complexity only as far as practical**, while matching input-space coverage and effective sampling exposure across cells. No architecture change is allowed before this map is read.

## Frozen cells

Task: `reduce: y -> y mod N`, using the public `benjaminW2025/one-layer-deeper` competition-faithful tokenizer and encoder harness.

- data seed: `45`
- model seed: `0`
- bit cells: `6, 7, 8, 9`
- model: `L2 d128`, default harness head count
- optimizer/lr/weight decay/warmup/grad clipping: unchanged harness defaults
- batch size: `256`
- target input-space coverage: `0.50`
- effective random-sampling epochs: `20`
- `n_train = floor(0.50 * N^2)` after deterministic modulus construction
- training steps: `ceil(20 * n_train / 256)`
- fresh evaluation size: `min(2000, N^2 - n_train)`, additionally capped to preserve strict train/fresh disjointness
- device: CPU is an explicit execution choice; results are capability diagnostics, not wall-clock comparisons

If a sampled bit cell cannot support the frozen train/eval split, reduce only `n_eval` to the largest legal fresh set. Do not alter coverage, model, or epochs.

## Per-example frozen descriptors

For every fresh evaluation input record:

- `N`
- `y`
- `q = floor(y / N)`
- `r = y mod N`
- decimal digit widths of `N`, `y`, `q`, and `r`
- normalized quotient `q/(N-1)` when defined
- exact correctness
- correct output digits / valid output digits

Aggregate results must include overall fresh digit/exact accuracy and deterministic quotient strata. Quotient bins are frozen as normalized quartiles `[0,.25), [.25,.5), [.5,.75), [.75,1]`; digit-width strata are also reported.

## Primary decision rule

Let `E_b` be fresh exact accuracy and `D_b` fresh digit accuracy for bit cell `b`, with their empirical constant-predictor chance baselines.

- **SUPPORT-DOMINANT:** all eligible larger cells retain positive digit excess and there is no material monotone deterioration across quotient complexity.
- **QUOTIENT-COMPLEXITY-WALL:** with matched 50% coverage and 20 sampling epochs, fresh digit excess falls materially as bit/quotient complexity rises, or a deterministic quotient stratum exhibits a sharp load-bearing boundary.
- **MIXED/LOCALIZED:** aggregate performance is not monotone but one or more quotient/digit-width strata show reproducible separation.
- **NULL_OPTIMIZATION:** any cell is flagged diverged or flat-from-start; do not interpret semantic capability from that cell.

A practical `material deterioration` flag is predeclared as a drop of at least `0.10` in fresh digit excess from the best lower-complexity eligible cell to a larger eligible cell. This threshold is descriptive, not a statistical significance claim.

## Causal/claim boundary

This is a matched CPU diagnostic of one representation and one small encoder. It can distinguish sparse support from quotient-complexity residuals in this world. It does not establish a universal arithmetic limitation, competition performance, or an architectural impossibility.
