# V127 — preserve fixed computed parameter acquisition result

**Status:** `REJECT_K3_INSUFFICIENT`

**Hosted run:** `31893855943`

**Job:** `95034027074`

**Artifact:** `v127-preserve-fixed-computed-parameter`

**Artifact ID:** `9249266284`

**Artifact digest:** `sha256:fa34e11ac0c4062e3a840c8571db6b62e8f2d5893130a791147130d28b1628bc`

## Precommit

`protocols/V127_PRESERVE_FIXED_COMPUTED_PARAMETER_ACQUISITION_PRECOMMIT.md`, commit `faf28beb05fd83991fcff67f69397bfb32daa2ae`.

## Frozen K3

K3 attempted to preserve a proper conclusion function application whenever every free variable in that application had a user name directly present in the top-level `inputNames` list.

## Result

The V126 MAP obstruction reproduced under exact V120 K2 (`rc=1`). K3 built cleanly and the ordinary package build succeeded, but the acquisition still failed:

- V126 MAP: FAIL (`rc=1`)
- V126 ID: PASS
- V125 U1: PASS
- V119 explicit/index: PASS
- V119 implicit/uniform: PASS
- V122 field-carrying: PASS
- V122 recursive: PASS

The MAP diagnostic remained the same `unk_0 = V126Lift a_1` / `Type 1` producer mismatch.

Because the primary acquisition failed, causal ablation was not run and K3 is rejected.

## Interpretation

The mechanism hypothesis was directionally close but the frozen *coordinate test* was wrong. At conclusion-linearization time the function application's dependency is a constructor-local forall variable; it is not yet named as the top-level producer input. Those variables become linked only through conclusion unification later.

Therefore direct user-name membership in `inputNames` cannot recognize an input-determined computed parameter at this stage.

This is not evidence against the computed-parameter bridge isolated by V126. It falsifies the specific K3 rule for deciding fixedness before unification.

## Next admissible refinement

A new prospectively frozen candidate must use structure available before unification: whether all free variables of the computed subterm occur in the constructor conclusion's **input argument positions** (all relation positions other than the frozen output indices). That criterion does not depend on eventual top-level variable names.
