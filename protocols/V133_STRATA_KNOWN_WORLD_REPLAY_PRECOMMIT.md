# V133 — exact K2+K5 Strata known-world replay precommit

Date frozen: 2026-08-16 NZST

## Prior state

V132 admitted K5 within the current pinned Specimen/protected-test scope:

`K2 FAIL -> K2+K5 PASS -> full 137/137 protected suite PASS -> remove K5 retaining K2 -> FAIL`.

The real Strata target used in V124 was inspected earlier, so it cannot count as blind held-out transfer. It remains useful as a known-world validation because V124 was the natural residual that initiated the V125-V132 refinement sequence.

## Question

Does the exact frozen admitted K2+K5 mechanism remove the previously observed direct-Strata obstruction without any target-specific modification?

## Frozen target

`SpecimenTest/V124DirectStrataLExpr.lean`

The target uses:

- real parameterized `Lambda.LExpr`;
- real `LExpr.HasTypeA` relation;
- no copied `LExprU` datatype;
- no copied `HasTypeAU` relation;
- 60 generated samples across five context/type requests checked by the frozen executable `v124TypeCheck` verifier.

## Sequence

1. Build the vendored Strata support module.
2. Apply exact frozen V120 K2 only and reproduce V124 failure.
3. Apply exact frozen V132 K5 with no modification.
4. Run the direct Strata target and all 60 verifier samples.
5. Ablate K5 while retaining K2 and require the original direct target to fail again.

No code, fixture, sample set, type checker, or mechanism may be changed after seeing target outcome.

## Gates

G1 K2-only V124 failure reproduces.
G2 K2+K5 direct Strata target compiles.
G3 all 60 frozen generated samples pass the unchanged executable type checker.
G4 removing K5 while retaining K2 restores V124 failure.
G5 K5 patch is byte-for-byte the same mechanism admitted by V132.

Verdict `PASS_V133_STRATA_KNOWN_WORLD_REPLAY` iff G1-G5 hold.

If K2+K5 still fails, record the next residual and do not modify K5 using Strata evidence without a new prospective discriminator outside Strata.

## Claim boundary

A pass supports known-world natural validation of the admitted representation distinction. It is not blind source-distinct transfer because the Strata workaround/target was already inspected before K5 was constructed.
