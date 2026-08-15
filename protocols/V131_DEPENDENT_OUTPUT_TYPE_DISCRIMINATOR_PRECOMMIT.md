# V131 — dependent output-type discriminator precommit

Date frozen: 2026-08-16 NZST

## RGRS state

V129 rejected the broad rule `input-determined => preserve`, because protected ordinary computed terms such as `x * x` must remain flattenable for lawful generated pattern matching.

V130 prospectively rejected the narrower direct-constructor-parameter hypothesis: both `V126Lift p` and `x * x` were classified as not occurring directly in constructor fixed-parameter argument positions.

Primary residual remains R6 Representation, with R5 Applicability as the admission problem.

## Question

Does the V126 computed application occupy a different structural role because it occurs in the **dependent type/family index of an output-position term**, while the protected `x * x` computation is an ordinary value expression rather than type-level family information?

## Frozen discriminator

Diagnostic only. No repair is permitted.

For every proper function application that the original linearizer would flatten:

1. take the constructor conclusion and its frozen `outputIndices`;
2. for each output-position conclusion argument, infer that argument's type;
3. classify whether the candidate application occurs structurally inside any inferred output-argument type;
4. separately record whether it occurs directly in the output value expression.

Run on:

- V126 MAP acquisition candidate `V126Lift p`;
- protected multiplication fixture `x * x`;
- V126 ID control.

The classifier may use only expression structure, output indices, and Lean type inference. No target-specific names may influence the classification rule.

## Gates

G1: V126 `V126Lift p` is classified as occurring in an output-position dependent type/family index.

G2: protected `x * x` is **not** classified as occurring in an output-position dependent type/family index.

G3: V126 ID remains a control without a corresponding problematic computed-type candidate.

G4: generation semantics remain unchanged; this experiment is instrumentation only.

Verdict `PASS_V131_DEPENDENT_OUTPUT_TYPE_DISCRIMINATOR` iff G1-G4 hold.

If G1 fails: reject the dependent-output-type hypothesis.
If G2 fails: the distinction is still too broad.

## Post-pass rule

Only after a pass may a K5 candidate be frozen. The admissible K5 family would be restricted to preserving input-determined proper applications **only when they serve as family/index information in an output term's dependent type**, while leaving ordinary computed value terms flattenable.

## Claim boundary

A pass identifies a structural separator only. It is not a repair, not a protected-suite success, and not natural transfer.
