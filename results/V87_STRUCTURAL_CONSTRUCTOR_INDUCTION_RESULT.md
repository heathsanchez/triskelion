# V87 Structural Constructor Induction — Attested Result

Status: **MIXED / NEGATIVE ON CAUSAL LEARNING CLAIM**

Primary workflow run: `31784802703`

Artifact: `9215089519` (`v87-structural-constructor-induction`)

Artifact SHA-256: `0181c97c3ce5f9efd9a39156491e64722715b2928165887702373e6a3ac1763c`

Primary verdict: `MIXED_STRUCTURAL_CONSTRUCTOR_INDUCTION_V87`

## Result

Training-side human fixes induced a structural grammar containing:
- `CONST_ROLE(str)` support 10
- `NAME_ROLE` support 4
- `NODETYPE Gt→GtE` support 1

On the sealed held-out split:
- K0 solved: `knapsack`
- K1 solved: `minimum_spanning_tree`, `hanoi`, `knapsack`, `depth_first_search`
- nominal new closure: 3 tasks

However the wrong-pair control solved the **exact same four tasks**. Therefore the held-out gain cannot be attributed to structure learned from the correct developmental history. It is explained by generic broadening of the constructor/search language.

## Binding interpretation

`broader constructor -> more solves` is not evidence of developmental constructor learning.

A constructor acquisition claim must beat a matched causally wrong/broadened constructor, not merely K0.
