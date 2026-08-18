# V125 — FX natural binder held-out qualification

**Status:** `PRECOMMITTED_BEFORE_SOURCE_BODY_INSPECTION`

## External candidate

Repository: `GrigoryEvko/FX`

Pinned public commit surfaced by GitHub code search: `e01b6e40bb6c283423c27bd7bcc1a6ac07700756`

Qualification file: `lean-fx-3/FX1Poly/Typed/Engine/HasTypeDesc/HasTypeDescGradedIntro.lean`

The candidate was selected from search metadata only after V124 hit a fixture/corpus ceiling. No source body from this file has been inspected in this experiment before this precommit.

## Frozen qualification rule

The target qualifies only if the pinned project contains a pre-existing independently authored typing/reduction/checking relation whose produced/runtime value inhabits an inductive family carrying at least one uniform non-Sort value parameter or index, and whose constructor application exposes the same implicit-uniform-vs-explicit-field reconstruction distinction frozen in V120.

The target must be genuine project functionality, not a benchmark fixture manufactured for this experiment.

If the structural shape is absent, record `CORPUS_CEILING_NO_FX_BINDER_TARGET` and stop without retuning.

## Frozen transfer gates

If qualification passes, apply the exact V120 K2 rule with no target-specific edits:

1. K0 must reproduce the relevant constructor-reconstruction failure.
2. Frozen K2 must repair it.
3. The unchanged target relation/checker must validate the produced value/result.
4. Existing relevant project tests/proofs must remain passing.
5. Removing only K2 must restore the failure.

All five are required for `PASS_V125_NATURAL_BINDER_TRANSFER`.

## Claim boundary

A pass would establish source-distinct natural-code transfer for this specific representation law only. Infrastructure/toolchain failures are null evidence; structural ineligibility is a corpus ceiling; neither may be relabeled as a semantic failure or success.
