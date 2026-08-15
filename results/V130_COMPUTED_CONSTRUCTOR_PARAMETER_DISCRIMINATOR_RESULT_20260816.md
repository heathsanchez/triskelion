# V130 — computed constructor-parameter discriminator result

**Status:** `REJECT_CONSTRUCTOR_FIXED_PARAMETER_ROLE`

**External substrate:** `heathsanchez/specimen`

**Valid hosted workflow run:** `31895252305`

**Job:** `95037479107`

**Artifact:** `v130-constructor-parameter-discriminator`

**Artifact ID:** `9249621542`

**Artifact digest:** `sha256:4bb5ada00eba351e3901759b20d22d7bbf93bae036006616efe1761d144ee07c`

## Precommit

`protocols/V130_COMPUTED_CONSTRUCTOR_PARAMETER_DISCRIMINATOR_PRECOMMIT.md`, commit `85ea27b22ca00be2fbec41a720e4a6502b85fff4`.

## Infrastructure attempts

Two earlier hosted attempts were R10 Infrastructure only:

1. `31894502734`: diagnostic instrumentation incorrectly treated a `Name` returned by `getAppFnArgs` as an `Expr` constant.
2. `31894979630`: diagnostic traversal was written in a way Lean could not prove terminating.

Both repairs changed only diagnostic implementation, not the frozen discriminator or scientific rule.

## Valid discriminator result

The final diagnostic run built and observed both frozen candidates:

- V126 MAP: `candidate=V126Lift p`, `ctor_fixed_parameter=false`.
- ordinary protected term: `candidate=x * x`, `ctor_fixed_parameter=false`.

The MAP acquisition still failed with the known hidden `V126Wrapped : Type 1` equality-producer residual. The multiplication control compiled under unchanged original flattening semantics.

Therefore:

- G1 — V126 computed application is in a constructor fixed-parameter position: **false**.
- G2 — multiplication is not in such a position: **true**.

Verdict: `REJECT_CONSTRUCTOR_FIXED_PARAMETER_ROLE`.

## Interpretation

V129 correctly showed that `input-determined` was too broad, but V130 shows that the useful V126 case is not separated by the narrower hypothesis "the computed application occurs directly in a constructor's fixed parameter argument".

The likely remaining structural location is a dependent **type/family index** carried by an output term or relation argument, rather than a direct constructor-argument occurrence. This must be tested explicitly before another repair is proposed.

## RGRS update

Primary residual remains `R6 Representation` with an `R5 Applicability` consequence: the system lacks the correct distinction between computed values that must remain flattenable for term/pattern matching and computed family/index information that should be carried as determined context.

No K5 repair is admitted from V130.
