# WHAKAPAPA CAUSALITY V1 — pre-outcome clarification addendum

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

This addendum resolves one topology ambiguity in the original precommit without changing a gate, budget, arm, world, or target family.

The frozen eight-node lineage contains a recombination event:

[
(L4,R4)ightarrow X5ightarrow X6.
]

After X5/X6 exist, L4 and R4 are no longer literal tips of the full graph. Therefore T2's phrase "current lineage tips belonging to distinct branches" is operationalized as:

> the tips of the **pre-recombination cut**, obtained by masking X5 and X6 and then applying the same generic `tips` operation.

Thus TRUE_MIN sees L4 and R4 as the two branch-frontier tips at the cut where recombination first became possible.

FLAT receives the same node contents and the same frozen T2 target but has no ancestry/cut relation, so it searches all unordered inherited capability pairs in stable ID order under the original fixed 8-pair budget.

SHAM and SEVERED compute the same pre-recombination-cut tips from their own supplied ancestry.

No outcome has been executed or inspected before this clarification.
