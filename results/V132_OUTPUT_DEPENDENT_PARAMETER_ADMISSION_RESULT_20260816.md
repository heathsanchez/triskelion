# V132 — output-dependent computed-parameter admission result

**Status:** `PASS_V132_OUTPUT_DEPENDENT_PARAMETER_ADMISSION`

**External substrate:** `heathsanchez/specimen`

**Hosted workflow run:** `31895952297`

**Job:** `95039182182`

**Head SHA:** `2bae78c95970ba98ffaaec3615a56d3b3bfef979`

**Artifact:** `v132-output-dependent-parameter-admission`

**Artifact ID:** `9249822294`

**Artifact digest:** `sha256:3b6abf0e5e35cc4ce5e42f060664ca65bf119db7bbbf1c84f08d3e90b8417eb8`

## Precommitted mechanism

K5 preserves a proper function application during conclusion linearization iff both conditions hold:

1. every free-variable dependency of the application occurs in relation-input positions;
2. the exact application occurs in the inferred dependent type/family of an output-position argument.

Ordinary computed value/pattern expressions remain on the original flattening path.

This mechanism was frozen only after:

- V129 rejected the broader input-determined K4 on protected tests;
- V130 rejected constructor-fixed-parameter role as the separator;
- V131 prospectively separated the V126 bridge from ordinary `x * x` using output-dependent-type role.

## Hosted result

Exact V120 K2 reproduced the V126 MAP obstruction (`rc=1`) with the expected hidden `V126Wrapped : Type 1` value and equality to `V126Lift a_1`.

Under K2 + K5 all frozen acquisition/control arms passed:

- V126 MAP acquisition: PASS (`rc=0`)
- V126 direct-ID control: PASS
- V125 direct `Type 1` control: PASS
- ordinary multiplication/function-call control: PASS
- V119 explicit/index control: PASS
- V119 implicit/uniform acquisition: PASS
- V122 field-carrying control: PASS
- V122 recursive control: PASS

The full ordinary Specimen protected surface also passed under K2 + K5, reaching `137/137 Built SpecimenTest`.

Causal ablation removed K5 while retaining exact K2. V126 MAP returned to FAIL (`rc=1`).

Workflow verdict: `PASS_V132_OUTPUT_DEPENDENT_PARAMETER_ADMISSION`.

## Causal chain

`K2 FAIL -> K2+K5 PASS -> full protected suite PASS -> remove K5 retaining K2 -> FAIL`.

This closes the scope failure exposed by V129 for the currently protected Specimen corpus.

## RGRS interpretation

The V124-V132 sequence is a worked RGRS chain:

1. natural known-world residual appears after an earlier repair;
2. coarse explanation (`Type 1`) is falsified;
3. computed-parameter bridge is prospectively isolated;
4. first repair coordinate (top-level names) is falsified;
5. broader input-position repair gains causal acquisition;
6. protected suite rejects that repair as over-broad;
7. constructor-parameter role is tested and rejected;
8. output-dependent-type role separates acquisition from protected counterexample;
9. conjunction of input-determined + output-dependent-type repairs acquisition, preserves the protected suite, and passes causal ablation.

The important developmental fact is that an initially useful mechanism was not retained after protected counterevidence. Counterevidence changed the representation rule rather than merely causing more tuning inside the same rule.

## Admission state

K5 is admitted **within the current pinned Specimen/protected-test scope**.

It is not yet evidence of blind source-distinct natural transfer. The previously inspected Strata case may now be replayed only as a known-world validation of whether the admitted mechanism removes the documented workaround barrier.

## Claim boundary

Supported claim:

> In a pinned real Lean metaprogramming system, residual-guided representation search isolated a missing distinction between ordinary computed terms and deterministic computed applications carried in output-dependent types. A prospectively narrowed mechanism causally expanded constructibility, survived the full current protected suite, and reverted under ablation.

Not established:

- arbitrary dependent-type support;
- arbitrary constructor-language invention;
- blind source-distinct natural transfer;
- open-ended self-improvement.
