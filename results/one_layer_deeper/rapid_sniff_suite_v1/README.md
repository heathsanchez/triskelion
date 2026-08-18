# RAPID_SNIFF_SUITE_V1

Forest-first 9-cell phase map: square vs reduce vs squaremod across matched-ish support/complexity regimes.

| task | bits | coverage | exact | chance | exact excess | digit | digit chance | digit excess |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| reduce | 6 | 24.49% | 0.3100 | 0.0800 | +0.2300 | 0.4821 | 0.2857 | +0.1964 |
| reduce | 7 | 30.19% | 0.0500 | 0.0300 | +0.0200 | 0.3187 | 0.1419 | +0.1769 |
| reduce | 8 | 24.45% | 0.0333 | 0.0200 | +0.0133 | 0.2686 | 0.2507 | +0.0178 |
| square | 10 | 35.71% | 0.0200 | 0.0100 | +0.0100 | 0.5993 | 0.1878 | +0.4114 |
| square | 12 | 43.10% | 0.0067 | 0.0067 | +0.0000 | 0.5847 | 0.2055 | +0.3792 |
| square | 14 | 24.80% | 0.0000 | 0.0033 | -0.0033 | 0.5026 | 0.1836 | +0.3190 |
| squaremod | 10 | 35.71% | 0.0000 | 0.0300 | -0.0300 | 0.0934 | 0.1730 | -0.0796 |
| squaremod | 12 | 43.10% | 0.0000 | 0.0133 | -0.0133 | 0.2068 | 0.2353 | -0.0285 |
| squaremod | 14 | 24.80% | 0.0000 | 0.0067 | -0.0067 | 0.1509 | 0.1731 | -0.0222 |

## Phase-map readout

- **reduce**: b6 cov=24.5% digitΔ=+0.196 exactΔ=+0.230; b7 cov=30.2% digitΔ=+0.177 exactΔ=+0.020; b8 cov=24.5% digitΔ=+0.018 exactΔ=+0.013
- **square**: b10 cov=35.7% digitΔ=+0.411 exactΔ=+0.010; b12 cov=43.1% digitΔ=+0.379 exactΔ=+0.000; b14 cov=24.8% digitΔ=+0.319 exactΔ=-0.003
- **squaremod**: b10 cov=35.7% digitΔ=-0.080 exactΔ=-0.030; b12 cov=43.1% digitΔ=-0.028 exactΔ=-0.013; b14 cov=24.8% digitΔ=-0.022 exactΔ=-0.007

## Decision

**Strong composition/interface sniff:** square and reduce each show substantial learnable structure somewhere in the mapped support band while squaremod remains weak.

## Claim boundary

Cheap CPU sniff only: bit sizes differ across reduction vs unit-space tasks to obtain comparable support. This is a phase-map diagnostic, not a competition-performance comparison.