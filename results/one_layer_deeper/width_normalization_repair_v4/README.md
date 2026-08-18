# WIDTH_NORMALIZATION_REPAIR_V4 result

**Verdict:** `NO_WIDTH_REPRESENTATION_REPAIR`

| N | arm | digit | chance | excess | exact | chance | excess | improvement vs original |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 299 | ORIGINAL | 0.63766 | 0.21344 | +0.42422 | 0.30850 | 0.00750 | +0.30100 | +0.00000 |
| 299 | PAD_X6 | 0.36786 | 0.21344 | +0.15442 | 0.05600 | 0.00750 | +0.04850 | -0.26980 |
| 323 | ORIGINAL | 0.33712 | 0.20561 | +0.13151 | 0.02800 | 0.00650 | +0.02150 | +0.00000 |
| 323 | PAD_X6 | 0.32803 | 0.20561 | +0.12242 | 0.02000 | 0.00650 | +0.01350 | -0.00910 |
| 377 | ORIGINAL | 0.25301 | 0.18273 | +0.07028 | 0.01450 | 0.00600 | +0.00850 | +0.00000 |
| 377 | PAD_X6 | 0.48770 | 0.18273 | +0.30498 | 0.05550 | 0.00600 | +0.04950 | +0.23470 |

- ORIGINAL N299-N323 boundary: `+0.29271`

## Frozen gates
- G0_REPRODUCE_BOUNDARY: `PASS`
- G1_N323_REPAIR: `FAIL`
- G2_N323_RESTORE_LEVEL: `FAIL`
- G3_N377_REPAIR: `PASS`
- G4_CONTROL_NOT_GLOBAL_MAGIC: `PASS`
- G5_TRAINING_VALID: `PASS`

## Claim boundary

Matched causal representation intervention in one pinned decimal modular-reduction/small-encoder setting; not a universal arithmetic, architecture, or developmental-intelligence claim.
