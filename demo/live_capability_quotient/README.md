# Live capability quotient demo

This is the replacement public demo for the earlier scripted DI mockup.

It does one thing only: execute the frozen V103 exact finite-world computation **live in the browser** and make the core result legible in seconds.

## What the viewer sees

1. The old language (variables/constants/XOR) has exact unbounded closure over only **16/256** three-input Boolean functions.
2. Acquisition uses hidden binary operator **1**; held-out uses a different literal operator **8**, permuted variables, and deeper programs.
3. Acquisition selects representatives **{1,11,13}**. The unseen held-out operator **8** is different, but all belong to the same old-language capability orbit **{1,2,4,7,8,11,13,14}**.
4. Under the CPython 3.12 CI-attested live run, retaining that capability class reduces exact held-out semantic-state expansions from **38,107** cold to **240** warm: **158.78×** less search.

The page executes `v103_live.py` through Pyodide. The CI workflow runs the same file under CPython 3.12 and checks all frozen scientific gates.

## Reproduction note

The historical V103 result file records a different literal optimum and 151.24× search compression from its original deterministic local execution. Running the frozen algorithm today under CPython 3.12 produces the values above while preserving every scientific gate and the quotient-level conclusion. The demo deliberately displays the live computation rather than hard-coding the historical headline numbers.

## Scientific claim boundary

This is an exact finite Boolean world. It supports closure obstruction, quotient-level capability identity under a literal representative change, held-out transfer, and exact search compression relative to the frozen affine effective language.

It does **not** establish representation-independent invention, unrestricted open-world capability construction, or general developmental intelligence.

The point of the demo is narrower and more defensible:

> A capability can survive a change in its literal implementation, and retaining that behavioral class can dramatically change the cost of future search.
