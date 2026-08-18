# Live capability quotient demo

This is the replacement public demo for the earlier scripted DI mockup.

It does one thing only: execute the frozen V103 exact finite-world computation **live in the browser** and make the core result legible in seconds.

## What the viewer sees

1. The old language (variables/constants/XOR) has exact unbounded closure over only **16/256** three-input Boolean functions.
2. Acquisition uses hidden binary operator **1**; held-out uses a different literal operator **8**, permuted variables, and deeper programs.
3. The system selects **{2,4}**, i.e. neither hidden operator, because those are cheaper representatives of the same old-language capability orbit **{1,2,4,7,8,11,13,14}**.
4. Retaining that capability class reduces exact held-out semantic-state expansions from **38,415** cold to **254** warm: **151.24×** less search.

The page executes `v103_live.py` through Pyodide. The CI workflow runs the same file under CPython 3.12 and asserts the frozen verdict and exact headline numbers.

## Scientific claim boundary

This is an exact finite Boolean world. It supports closure obstruction, quotient-level capability identity under a literal representative change, held-out transfer, and exact search compression relative to the frozen affine effective language.

It does **not** establish representation-independent invention, unrestricted open-world capability construction, or general developmental intelligence.

The point of the demo is narrower and more defensible:

> The learned object need not be the literal operator. Retaining the behaviorally invariant capability class can change the cost of future search dramatically.
