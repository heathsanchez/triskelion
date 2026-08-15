# V123 — Cedar natural held-out qualification and transfer precommit

**Status:** FROZEN BEFORE V123 TARGET INSPECTION

## Motivation

V120 froze `CARRY_IMPLICIT_FIXED_PARAMETER`; V121 showed full current Specimen-suite preservation. The missing capstone gate is source-distinct natural transfer.

Use the independently structured Cedar example already vendored in Specimen as a natural held-out world. The K2 mechanism was frozen before any V123 Cedar target search. Existing Cedar test logs may have exposed relation names but no V123 target body has been selected or used to alter K2.

## Frozen source world

Repository: `heathsanchez/specimen`.

Natural source namespace/module: `SpecimenTest.CedarExample.Cedar`.

Exclude:

- every V117–V122 fixture;
- Strata as primary evidence;
- any declaration already explicitly used as a V120/V121 acquisition arm;
- any synthetic declaration added after the V120 K2 freeze.

## Mechanical candidate order

Inspect Cedar declarations only after this protocol is committed.

Candidate relations are sorted lexicographically by fully-qualified declaration name and must satisfy all of:

1. declaration is an existing `inductive ... : Prop` relation from the pinned Cedar source file;
2. it has at least one runtime/value input before an output argument;
3. its output argument type is an application of an inductive family with at least one uniform **non-Sort** parameter;
4. the relevant output-family constructor telescope contains an implicit/strict-implicit/instance-implicit leading parameter corresponding to that fixed family parameter;
5. target signature can be expressed as an ordinary Specimen constrained producer `fun inputs => ∃ output, Relation inputs output` without changing the Cedar relation.

If no declaration qualifies, return `CORPUS_CEILING_NO_CEDAR_BINDER_TARGET`; do not invent a target.

## Qualification and target selection

For each structurally eligible relation in frozen lexical order:

1. create only the derivation invocation needed to ask Specimen for the constrained producer; do not alter the Cedar relation;
2. execute under K0;
3. classify the failure.

The primary target is the **first** structurally eligible relation whose K0 failure is causally compatible with the V118 binder-role obstruction (constructor over-application / fixed-parameter reconstruction), not a missing unrelated typeclass, unsupported syntax, timeout, or unrelated scheduler failure.

If all structurally eligible relations fail only for unrelated reasons or already pass K0, return `CORPUS_CEILING_NO_QUALIFIED_CEDAR_TARGET`.

No target switching based on K2 success is allowed.

## Frozen intervention test

After a primary target is fixed from K0 qualification:

- apply the exact unchanged V120 K2 patch;
- rerun the exact same Cedar derivation/verifier;
- then ablate K2 and rerun again.

## Gates

- G0: pinned Cedar/Specimen world builds under K0.
- G1: a natural Cedar relation qualifies structurally.
- G2: selected target K0 fails for the binder-role mechanism.
- G3: exact frozen K2 passes the unchanged target.
- G4: ablating K2 restores the target failure.
- G5: ordinary protected Specimen tests remain passing under K2 (V121 may be cited if branch/source state is unchanged except V123 harness files).
- G6: K2 source is byte-identical to the V120 frozen mechanism.

`PASS_V123_NATURAL_HELDOUT` requires G0–G6.

## Claim boundary

A pass would support:

> A constructor-representation mechanism constructed from a prospectively isolated acquisition residual transferred unchanged to an independently structured pre-existing Cedar relation, changed K0-failing constructibility to verifier-accepted constructibility, and lost that capability again under ablation.

This would be the first strong source-distinct natural constructor-development capstone in this line.

It would still not establish arbitrary open-ended meta-language invention or universal transfer.
