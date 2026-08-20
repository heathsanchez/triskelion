# V135 — Daniel residual-gated constructor growth precommit

Date frozen: 2026-08-20 NZST

## Purpose

This protocol is designed to answer Daniel's specific question, not to create another toy reachability result.

The question is whether an admitted verified repair can change the space of possible developmental continuations by exposing a residual from which a second repair becomes constructible. The earlier Daniel closure-depth reproduction established bounded reachability development, but it did **not** establish strict second-generation constructibility because the later repair was already syntactically formable in the cold constructor language.

V135 therefore tests residual-gated constructor growth in the real Lean metaprogramming lineage around Specimen:

- `D0 = K2`
- `O1 = K5`
- `D1 = K2 + K5`
- `R2 = specialization-before-instance-synthesis residual`
- `O2 = K6`, if and only if it is produced by the frozen constructor rule below.

## Authoritative prior facts

The experiment treats the following repository facts as prior evidence, not as new V135 claims:

1. V132 admitted K5 in the pinned Specimen scope: `K2 FAIL -> K2+K5 PASS -> 137/137 protected suite PASS -> remove K5 retaining K2 -> FAIL`.
2. V133 replayed K2+K5 on known-world Strata and did **not** solve it, but changed the residual from the earlier hidden computed-family / `Type 1` obstruction to parameter-dependent typeclass synthesis over symbolic family parameters.
3. V134 was frozen as a controlled discriminator for that residual, unrelated to Strata, with no new repair allowed.

V135 does not claim that V132-V134 already prove second-generation constructibility.

## What would count as a Daniel-positive result

A positive result requires all of the following:

```text
R2 not observable from D0 under the frozen V134 discriminator
R2 observable from D1 under the frozen V134 discriminator
K6 not constructible from the D0 residual record under the frozen constructor rule
K6 constructible from the D1/R2 residual record under the frozen constructor rule
D1+K6 passes the V135 acquisition target and protected controls
Removing K6 restores the V135 failure
The verifier contract is unchanged throughout
```

The central constructibility claim is:

```text
K6 ∉ Construct_B(Obs(D0))
K6 ∈ Construct_B(Obs(D1))
```

This is stronger than a model failing to guess K6 cold. It must follow from the absence of the frozen residual pattern required by the constructor rule.

## Frozen residual schema R2

The V135 constructor rule may only fire when the residual record contains all of the following normalized fields:

```json
{
  "residual_family": "specialization_before_instance_synthesis",
  "fixed_top_level_parameter": true,
  "constructor_local_symbolic_parameter": true,
  "downstream_instance_requested_over_symbolic_parameter": true,
  "specialized_concrete_type_has_available_instance": true,
  "failure_is_not_universe_mismatch": true,
  "failure_is_not_constructor_overapplication": true,
  "failure_is_not_parser_or_build_error": true
}
```

The canonical diagnostic example is an obligation of the form:

```text
Arbitrary a.Meta
```

when the target has already fixed `a = P0` and `P0.Meta` is definitionally `Unit`, with an available `Arbitrary Unit` instance.

## Frozen constructor rule: `SpecializeBeforeInstanceSynthesis`

If and only if R2 is present, the constructor may propose the following repair family:

```text
Before synthesizing field-generation/typeclass evidence for a constructor field whose type depends on a constructor-local family parameter, first propagate any already-fixed top-level relation/target parameter equality into the field type. Request the instance for the specialized concrete field type rather than the symbolic local family projection.
```

Permitted implementation shape:

1. detect that a constructor-local parameter is definitionally fixed by the target/relation input;
2. substitute or normalize that parameter before downstream instance synthesis;
3. preserve the generic path when no fixed target parameter is available;
4. do not add target-specific instances;
5. do not mention Strata-specific names;
6. do not weaken the verifier or generated target.

Forbidden implementation shape:

1. adding a bespoke `Arbitrary` instance for the acquisition target;
2. special-casing `P0`, `Unit`, `Metadata`, `IDMeta`, Strata, or any target name;
3. accepting failed instance synthesis as success;
4. changing the verifier contract;
5. replacing K2/K5 wholesale with a different derivation path;
6. using protected target information to design the repair.

## Two-state residual reachability test

Run the exact V134 controlled family twice:

- `D0 = K2`
- `D1 = K2 + K5`

Record normalized residuals for the GENERIC and FIXED arms.

### Gate R1 — D0 does not expose R2

`PASS_R1` iff D0 does not produce the full R2 schema above on the FIXED arm.

Allowed outcomes:

- old K2 obstruction appears earlier;
- build/runner invalidity is recorded as apparatus failure;
- FIXED passes, in which case V135 is null because the downstream residual is not forced.

### Gate R2 — D1 exposes R2

`PASS_R2` iff D1 produces the full R2 schema on the FIXED arm while the GENERIC arm remains parameter-dependent or legitimately requires generic field evidence.

If D1 FIXED passes, verdict is `NULL_R2_NOT_PRESENT`.
If both arms fail for a shared unrelated reason, verdict is `INVALID_DISCRIMINATOR`.

## Frozen constructibility test

Run the same residual-to-constructor evaluator on both normalized residual records.

### Gate C0 — cold non-constructibility

`PASS_C0` iff the frozen constructor rule cannot emit K6 from D0 evidence because at least one required R2 field is absent.

This must be reported as structural non-constructibility, not as sampling failure.

### Gate C1 — developed constructibility

`PASS_C1` iff the frozen constructor rule emits exactly one repair family from D1 evidence:

```text
SpecializeBeforeInstanceSynthesis
```

This is the only admitted K6 candidate for V135.

## Verification gates for K6

After K6 is implemented from the emitted repair family:

### Gate V1 — acquisition

D1+K6 must pass the V135 FIXED acquisition arm.

### Gate V2 — generic control

The GENERIC arm must not become unsoundly specialized. It may still fail for missing generic field evidence, or pass only with legitimate generic evidence.

### Gate V3 — protected suite

The current pinned protected Specimen suite must pass under D1+K6.

### Gate V4 — local K6 ablation

Removing K6 while retaining exact D1 must restore the V135 FIXED failure.

### Gate V5 — ancestor route ablation

The route to K6 must disappear when K5 is absent:

```text
Construct_B(Obs(K2)) does not emit K6
Construct_B(Obs(K2+K5)) emits K6
```

If the implemented K6 can be manually inserted into K2 and pass, that does not by itself falsify the developmental claim. But the V135 Daniel claim must be phrased as residual-gated constructibility, not as semantic impossibility of the final patch existing in source code.

## Verdict table

- `PASS_V135_DANIEL_RESIDUAL_GATED_CONSTRUCTOR`: R1, R2, C0, C1, V1, V2, V3, V4, V5 all pass.
- `NULL_R2_NOT_PRESENT`: D1 does not expose the R2 residual in the controlled V134 family.
- `NO_CONSTRUCTIBILITY_DIFFERENCE`: both D0 and D1 emit K6, or neither emits K6.
- `LOCAL_REPAIR_ONLY`: K6 passes acquisition but fails protected suite or ablation.
- `INVALID_DISCRIMINATOR`: V134 family fails for an unrelated shared reason.
- `APPARATUS_FAILURE`: build, runner, dependency, or environment failure prevents semantic interpretation.

## Claim boundary

A V135 pass would support:

> In a pinned Lean metaprogramming lineage, admitted repair K5 exposed a verifier residual not reachable in the prior developmental state. A frozen residual-gated constructor rule then produced K6 from the K5-exposed residual but not from the cold residual record. K6 passed acquisition/protected checks and ablation restored failure. Thus the first verified repair changed the set of constructible next developmental continuations under the frozen constructor rule.

A V135 pass would **not** establish:

- arbitrary autonomous invention of K6;
- universal dependent-type support;
- open-ended self-improvement;
- that K6 was impossible for a human to write cold;
- that final source-code insertion of K6 could not work without K5;
- a categorical theorem about regime transitions.

The mathematical object for Daniel is the experimentally observed distinction:

```text
Next_B(D0) != Next_B(D1)
```

where `Next_B(D)` is defined by observable verifier residuals plus the frozen residual-to-constructor rule, not by retrospective human imagination.
