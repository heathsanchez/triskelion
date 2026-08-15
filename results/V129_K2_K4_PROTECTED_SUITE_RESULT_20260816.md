# V129 — K2+K4 protected-suite validation result

**Status:** `REJECT_K4_HARMFUL`

**External substrate:** `heathsanchez/specimen`

**Hosted workflow run:** `31894305039`

**Job:** `95035099934`

**Artifact:** `v129-k2-k4-protected-suite`

**Artifact ID:** `9249390803`

**Artifact digest:** `sha256:2ba251233bc549876955bb490e2b1fded6b18196f35523998bea8e21596b959b`

## Precommit

`protocols/V129_K2_K4_PROTECTED_SUITE_PRECOMMIT.md`, commit `9174f76f4d1fc290f79ebff43d187b91c3794467`.

## Result

K0 ordinary build/test passed and reached `137/137 Built SpecimenTest`.

Exact frozen V120 K2 + V128 K4 built the package, but the unfiltered ordinary protected test suite failed. Therefore K4 is not admissible as a general capability despite the causal V128 acquisition result.

Observed protected failures included:

- `DeriveArbitrarySuchThat.FunctionCallsTest`
- `DeriveArbitrarySuchThat.DependentArgs`
- `DeriveArbitrarySuchThat.MultiOutputTest`
- `DeriveDecOpt.FunctionCallsTest`
- `DeriveDecOpt.DeriveRegExpMatchChecker`
- `DeriveArbitrarySuchThat.SimultaneousMatchingTests`
- `StrataLexprGen`

Representative diagnostics show the mechanism is over-broad: preserving input-determined proper function applications can leave non-constructor computed terms in generated pattern positions (for example multiplication), causing invalid/inaccessible pattern variables; in other cases expected flattened unknowns disappear from the scheduler's `UnknownMap`.

Because the protected suite failed, the workflow correctly skipped the V128 acquisition recheck and returned failure.

## Interpretation

V128 remains valid as a **controlled causal acquisition** on its frozen discriminator: K2 FAIL -> K2+K4 PASS -> K4 ablation FAIL. V129 shows that the K4 rule is too broad for admission.

The negative law is now sharper:

> `input-determined` is necessary to avoid independently generating a computed family parameter, but it is not sufficient to decide that an arbitrary proper application should bypass conclusion flattening.

Some input-determined applications are computational expressions required to be flattened so generated pattern matching remains lawful.

## Developmental state

K4 is **rejected**, not retained. No Strata replay is admissible yet.

The next move must discriminate the V126 computed **family-parameter** use from ordinary computed **term/pattern** uses that protected tests rely on flattening. That distinction must be prospectively frozen and validated before any new repair candidate is admitted.
