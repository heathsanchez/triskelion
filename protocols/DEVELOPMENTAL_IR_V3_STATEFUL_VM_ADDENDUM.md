# DEVELOPMENTAL IR V3 — pre-outcome implementation addendum

Status: **FROZEN BEFORE EXECUTION**

V3 uses the already exact D+GROUND implementations of Boolean and 8-bit ALU operators established on the branch ancestry. To keep the 1,500-task, 65,536-row, 24-step stateful experiment tractable without changing the scientific object:

1. Each frozen VM template is compiled once into an exact 24-step **D-circuit skeleton** with symbolic initial-state leaves.
2. LOCAL_DAG cost is the exact unique D-node count of that skeleton plus the exact inherited parent-circuit cost substituted at the symbolic input leaves.
3. DEVELOPMENTAL and SYNTAX_ISA replace eligible inherited output-bit leaves by unit-cost CAP leaves before the same template skeleton is accounted.
4. Exact program semantics are evaluated independently over all 65,536 input pairs with bit-vector state masks, including PC, RAM, branch masks, and halt masks.
5. Direct representative template instances are additionally checked against the D-circuit skeleton semantics.
6. The cost certificate therefore measures the exact frozen abstract D-circuit model without repeatedly materializing billions of equivalent D nodes for each task.

No gate threshold, task count, template family, step horizon, or correctness condition is changed.
