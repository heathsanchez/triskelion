# SQUARE_EXACTNESS_CARTOGRAPHY_V1

Frozen rapid 16-cell map. One model per alignment; both are trained for 500 steps on exactly 30% unique support inside every structural basin, with cell-balanced minibatches.

| alignment | digits | carry | width | coverage | exact | digit |
|---|---:|---|---|---:|---:|---:|
| absolute | 3 | high | expand | 30.0% | 0.007 | 0.568 |
| absolute | 3 | high | stable | 29.8% | 0.009 | 0.656 |
| absolute | 3 | low | expand | 30.2% | 0.108 | 0.748 |
| absolute | 3 | low | stable | 30.4% | 0.154 | 0.799 |
| absolute | 4 | high | expand | 30.0% | 0.000 | 0.485 |
| absolute | 4 | high | stable | 30.0% | 0.003 | 0.563 |
| absolute | 4 | low | expand | 30.2% | 0.095 | 0.797 |
| absolute | 4 | low | stable | 30.1% | 0.055 | 0.764 |
| place | 3 | high | expand | 30.0% | 0.010 | 0.587 |
| place | 3 | high | stable | 29.8% | 0.044 | 0.705 |
| place | 3 | low | expand | 30.2% | 0.108 | 0.797 |
| place | 3 | low | stable | 30.4% | 0.256 | 0.825 |
| place | 4 | high | expand | 30.0% | 0.000 | 0.507 |
| place | 4 | high | stable | 30.0% | 0.005 | 0.605 |
| place | 4 | low | expand | 30.2% | 0.162 | 0.812 |
| place | 4 | low | stable | 30.1% | 0.183 | 0.830 |

## Largest matched contrasts

- Largest exact-accuracy contrast: `('carry', 'place', 3, 'stable', -0.2121624687996369, -0.11977157552378792)`
- Largest digit-accuracy contrast: `('carry', 'absolute', 4, 'expand', -0.0945945945945946, -0.31260979729729726)`

## Frozen decision rules

- Carry obstruction candidate: matched low→high carry exact drop >= 0.15.
- Width obstruction candidate: matched stable→expand exact drop >= 0.15.
- Alignment repair candidate: place-value exact gain >= 0.15 in an affected basin.
- Otherwise treat as distributed/interaction residual and use position vectors for the next separator.

## Claim boundary

Seed-0 CPU sniff only. This identifies candidate structural boundaries; any >=15pp landmark must be repeated on >=2 further seeds before promotion to a causal obstruction.