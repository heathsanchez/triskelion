# REDUCTION_COMPLEXITY_MAP_V2 result

**Verdict:** `QUOTIENT_COMPLEXITY_WALL`

| bits | N | coverage | steps | digit | chance | excess | exact | chance | excess |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 35 | 49.959% | 48 | 0.24286 | 0.24476 | -0.00190 | 0.06036 | 0.03752 | +0.02284 |
| 7 | 91 | 49.994% | 324 | 0.32244 | 0.11952 | +0.20292 | 0.06250 | 0.01550 | +0.04700 |
| 8 | 143 | 49.998% | 799 | 0.45897 | 0.25426 | +0.20471 | 0.08200 | 0.01150 | +0.07050 |
| 9 | 377 | 50.000% | 5552 | 0.23486 | 0.18424 | +0.05062 | 0.01800 | 0.00650 | +0.01150 |

## Quotient quartiles

### bits=6 N=35
- Q0_25: n=165, digit=0.20789, exact=0.03636
- Q25_50: n=145, digit=0.27126, exact=0.09655
- Q50_75: n=159, digit=0.24354, exact=0.07547
- Q75_100: n=144, digit=0.25296, exact=0.03472
### bits=7 N=91
- Q0_25: n=483, digit=0.23568, exact=0.04969
- Q25_50: n=497, digit=0.33192, exact=0.05835
- Q50_75: n=521, digit=0.34588, exact=0.06334
- Q75_100: n=499, digit=0.37284, exact=0.07816
### bits=8 N=143
- Q0_25: n=498, digit=0.42680, exact=0.07028
- Q25_50: n=485, digit=0.47403, exact=0.09278
- Q50_75: n=517, digit=0.49047, exact=0.09478
- Q75_100: n=500, digit=0.44414, exact=0.07000
### bits=9 N=377
- Q0_25: n=519, digit=0.26000, exact=0.01927
- Q25_50: n=467, digit=0.24746, exact=0.02141
- Q50_75: n=506, digit=0.25126, exact=0.01779
- Q75_100: n=508, digit=0.18069, exact=0.01378

## Decision flags

- material drop flags: `[{'bits': 9, 'drop_from_best_lower': 0.15409192088445153}]`
- all eligible digit excess positive: `False`
- monotone nonincreasing digit excess: `False`

## Claim boundary

Matched CPU diagnostic of one representation and one small encoder; not a universal arithmetic or architecture claim.
