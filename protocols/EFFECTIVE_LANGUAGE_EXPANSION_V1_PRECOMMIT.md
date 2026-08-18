# Effective Language Expansion V1 — prospective precommit

Frozen before executing the experiment.

## Question

Given a fixed general construction substrate `U` and a strictly smaller installed effective language `L0`, can verifier counterexamples force synthesis of a reusable program that is **not enumerated as a candidate operator in L0**, admit that program as a new effective primitive, and thereby make a second capability reachable that was impossible in the old closure?

This is a bounded test of **endogenous effective-language growth**, not a claim of substrate-free invention.

## World

All semantics are exact Boolean functions of three inputs, represented extensionally by their 8-row truth tables.

### Installed effective language L0

Terminals: `0, 1, x, y, z`.

Installed combinators: `NOT`, `XOR`.

`Cl(L0)` is computed to exact fixed point. It must contain exactly the 16 affine Boolean functions.

### General construction substrate U

The meta-constructor may build arbitrary expression trees from the same terminals plus generic primitives:

- unary `NOT`
- binary `XOR`
- binary `AND`

`U` is available **only to the construction process**. Ordinary solving before admission is restricted to `L0`.

No candidate list of target operators, semantic names, repair templates, quotient classes, or target-specific macros is supplied.

## Mechanical target selection

To prevent hand-selection of an easy positive:

1. Enumerate minimal semantic expressions in `U` up to AST size 7.
2. Eligible acquisition targets are semantic functions that:
   - are not in `Cl(L0)`;
   - have minimal `U` expression size 5..7.
3. Rank eligible functions by SHA-256 of `"METALOGIC_EFFECTIVE_LANGUAGE_EXPANSION_V1:<function-id>"` and select the first.

The selected target identity is therefore determined by the frozen algorithm, not chosen after inspection.

## Gate A — old-language obstruction

Compute exact `Cl(L0)` before construction.

PASS A iff the mechanically selected acquisition target is not in `Cl(L0)`.

This distinguishes expressive obstruction from ordinary search failure in this finite world.

## Gate B — counterexample-guided synthesis

The constructor does not receive the target expression.

It begins with no target-labelled rows. At each round:

1. choose the smallest/lexicographically earliest `U` expression consistent with all verifier counterexamples seen so far;
2. seal that proposal;
3. the independent extensional verifier compares it against the hidden target truth table;
4. on failure, return only the first mismatching input/output row;
5. repeat.

PASS B iff this process reaches an exact semantic match within the frozen `U` size bound.

No semantic hint or target expression is returned by the verifier.

## Gate C — admission changes the effective language

If B passes, install the sealed synthesized program as a new primitive `K`, creating `L1 = L0 + {K}`.

The admitted object is the verified behavior of `K`; its literal expression remains provenance, not identity.

## Gate D — changed future reachability

Mechanically enumerate expressions in `L1` up to AST size 6.

Eligible downstream targets `O2` are functions that:

- are absent from exact `Cl(L0)`;
- are reachable in the bounded `L1` enumeration;
- are not identical to `K`.

Rank by SHA-256 of `"METALOGIC_EFFECTIVE_LANGUAGE_EXPANSION_V1:O2:<function-id>"` and select the first.

PASS D iff:

- `O2` is unreachable in `Cl(L0)`;
- `O2` is reached after installing `K`.

## Gate E — causal ablation

Remove only `K`, restoring `L0`, and rerun downstream reachability.

PASS E iff `O2` again becomes unreachable.

Restore exactly the sealed `K` and rerun.

PASS E-restore iff `O2` is reachable again.

## Frozen verdict

`PASS_EFFECTIVE_LANGUAGE_EXPANSION_V1` iff A, B, C, D, E and E-restore all pass.

Otherwise return a named negative/obstruction. No target-specific rescue, grammar extension, changed size bound, or second seed is allowed after seeing the result.

## Claim boundary

A pass supports only this bounded claim:

> Under a fixed general construction substrate, verifier counterexamples can drive synthesis and admission of a non-preenumerated effective-language construct, and that admitted construct can causally change future reachability.

It does **not** establish arbitrary ontology invention, open-world self-modification, neural learning, representation-independent novelty, or general intelligence.
