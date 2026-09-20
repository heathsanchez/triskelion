# CONSEQUENCE × WHAKAPAPA × FORM V1 — retry 2 implementation addendum

Status: **FROZEN AFTER THREE NON-SCIENTIFIC HARNESS TIMEOUT/CANCELLATION RUNS AND BEFORE RETRY IMPLEMENTATION**

The scientific precommit at `37daa6bf746d57aa8f5dc295f16d14eb44393190` and the bounded form-bank retry addendum remain unchanged.

The latest run reached the workflow's 30-minute timeout while still in the experiment step. No result file was validated or committed, so there is still no scientific outcome.

Profiling by code inspection identifies the dominant remaining cost as repeated graph traversal, not the bounded form bank:

- every disjoint-lineage mating proposal recomputes full ancestor sets;
- recombinant audits recompute ancestry repeatedly;
- revocation-target selection recomputes complete descendant sets for every candidate;
- several equivalent full simulations are rerun only to recover already available cost fields.

This addendum permits only **exact memoization / indexing of already-defined graph relations**:

1. Each capability stores an exact ancestry bitset equal to the transitive closure of its recorded parent edges plus itself.
2. Disjoint-lineage tests use bitset intersection rather than graph traversal.
3. Each capability stores an exact descendant count updated when new descendants are admitted. This is used only to rank the revocation target; the actual revocation cone is still enumerated from child edges once after selection.
4. Already computed simulation objects/costs may be reused instead of rerunning an extensionally identical simulation.
5. Deterministic replay remains required and must reproduce the same scientific hashes.

No parent-selection rule, mating frequency, consequence, form candidate, gate, threshold, revocation rule, or workload episode is changed.

The retry therefore tests the same scientific object with a faster exact graph index.
