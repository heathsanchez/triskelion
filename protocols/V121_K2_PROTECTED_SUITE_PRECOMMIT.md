# V121 — K2 protected-suite validation precommit

**Status:** FROZEN BEFORE EXECUTION

## Starting point

V120 acquisition passed with the frozen generic mechanism `CARRY_IMPLICIT_FIXED_PARAMETER` on `heathsanchez/specimen`.

The mechanism is frozen by Specimen branch `v120-binder-aware-fixed-parameter`, patch script `scripts/v120_apply_binder_aware_fixed_parameter.py`, and acquisition head `12cebb1d004126685cd2509f9f25a5c612a1c176`.

## Question

Does the exact V120 K2 mechanism preserve the existing Specimen test library and default build, rather than merely fitting the two acquisition fixtures?

## Frozen execution

On the unchanged V120 branch checkout:

1. run the ordinary default Specimen build before K2;
2. run the ordinary Specimen test runner before K2;
3. apply the exact frozen V120 patch script with no modification;
4. rebuild `Specimen.DeriveConstrainedProducer`;
5. run the ordinary default Specimen build after K2;
6. run the ordinary Specimen test runner after K2;
7. rerun the V119 explicit/index and implicit/uniform acquisition arms to ensure the V120 acquisition property remains true.

No test files may be modified, skipped, filtered, or expected-output adjusted.

## Gates

- G0: K0 default build passes.
- G1: K0 ordinary test runner passes.
- G2: frozen K2 patch applies and compiles.
- G3: K2 default build passes.
- G4: K2 ordinary test runner passes.
- G5: K2 explicit/index matched control passes.
- G6: K2 implicit/uniform acquisition passes.

`PASS_V121_PROTECTED_SUITE` requires G0–G6.

Any regression in the ordinary test runner is `HARMFUL_K2_REGRESSION` even if the acquisition fixtures pass.

## Claim boundary

A pass establishes protected-suite preservation for the current Specimen test library plus the V120 acquisition pair. It still does not establish source-distinct constructor-language growth or blind natural held-out transfer.
