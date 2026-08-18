# V124 — Ix natural binder held-out qualification

**Status:** `PRECOMMITTED_BEFORE_SOURCE_BODY_INSPECTION`

## Motivation

V120 froze a generic binder-aware constructor reconstruction law after acquisition and protected-control testing:

`EXPLICIT CONSTRUCTOR ARGUMENT != IMPLICIT UNIFORM PARAMETER`.

V123 then stopped at a corpus ceiling because Cedar had no qualifying natural output family with a uniform non-Sort value parameter. The next deciding test is therefore a genuinely source-distinct natural Lean world with indexed/value-parameterized typing machinery.

## Frozen external candidate

Repository: `argumentcomputer/ix`

Pinned public commit surfaced by GitHub code search: `6e10865ce0750523917b4b1adf5a833dd6d93a8f`

Qualification file: `Ix/Tc/Verify/NatFixture.lean`

The candidate was selected from GitHub search metadata for `inductive HasType Nat Vector Ty`; no source body from this file has been inspected in this experiment before this precommit.

## Frozen qualification rule

Inspect only the pinned source after this precommit. The file qualifies only if it contains, directly or through its imported project definitions, an existing independently authored relation or checker whose produced/runtime value inhabits an inductive family carrying at least one uniform non-Sort value parameter or index that creates the same constructor-reconstruction distinction tested by V120.

A qualifying target must be pre-existing project functionality. Do not manufacture a target or alter the family solely to make V120 applicable.

If no such target exists, record `CORPUS_CEILING_NO_IX_BINDER_TARGET` and stop this branch of the search.

## Frozen transfer gate if qualification passes

Use the exact frozen V120 K2 mechanism, without target-specific edits:

- omit a leading constructor parameter from emitted explicit constructor syntax only when its binder is implicit, strict-implicit, or instance-implicit;
- preserve default/explicit constructor binders;
- leave search limits and all unrelated constructor filtering unchanged.

Required outcome sequence:

1. **K0 discriminator:** unmodified mechanism fails on the qualifying natural target for the same constructor-reconstruction reason.
2. **K2 transfer:** frozen V120 K2 succeeds on that target without target-specific changes.
3. **Semantic verification:** produced value/result is accepted by the target's unchanged checker/relation/tests.
4. **Protected preservation:** relevant existing project tests remain passing.
5. **Causal ablation:** removing only K2 restores the target failure.

Only all five gates justify `PASS_V124_NATURAL_BINDER_TRANSFER`.

## Negative controls / claim boundary

A failure for unrelated imports, toolchain drift, unsupported syntax, or unavailable harness is infrastructure/null evidence, not semantic falsification.

A target that does not possess the frozen structural shape is a corpus ceiling, not evidence against K2.

A successful transfer is evidence only for source-distinct natural-code transfer of this specific binder-role distinction. It does not establish arbitrary operator invention, unrestricted autonomous software development, or broad natural-code generality.
