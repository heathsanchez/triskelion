# Capability Orbit Identity and Reachability Preorder

Date: 2026-08-15 NZST

This note sharpens the quotient/identity claim into an algebraic statement that is independent of the particular finite examples.

It complements `theory/VERIFIER_QUOTIENT_LAWS.md`, which handles verifier-indexed observational equivalence/refinement. The present note handles **identity modulo old capability** and the **developmental reachability order**.

## 1. Setup

Let `M` be a monoid of executable transformations/behaviours under composition.

Let `A <= M` be the current capability state, assumed composition-closed and containing identity.

Let `U(A)` be the units of `A`: elements of `A` with inverses also in `A`.

Let `O` be a candidate new operator/behaviour of compatible type.

Write

`Cl(A ∪ {O})`

for the smallest composition-closed capability set containing `A` and `O`.

For typed/multi-argument operators, pre/post coordinate transformations are understood at the compatible interfaces; the unary notation below is only for compactness.

## 2. Old-capability orbit identity

Define

`O1 ~_A O2`

when there exist `u,v in U(A)` such that

`O2 = u ∘ O1 ∘ v`.

For multi-input operators, `v` may be a product/permutation of invertible input-coordinate transformations already realizable by `A`.

The equivalence class is the old-capability orbit

`[O]_A`.

When verifier authority matters, the operational object is indexed jointly:

`[O]_(A,V)`.

The verifier index means only distinctions authoritative under `V` may be used operationally; see `VERIFIER_QUOTIENT_LAWS.md`.

## 3. Theorem — orbit representatives have identical generated closure

### Statement

If `O1 ~_A O2`, then

`Cl(A ∪ {O1}) = Cl(A ∪ {O2})`.

Therefore two literal operators in the same old-capability orbit have exactly the same future composition reachability.

### Proof

Suppose

`O2 = u ∘ O1 ∘ v`

with `u,v in U(A)`.

Because `u,v in A`, and `Cl(A ∪ {O1})` contains `A` and is closed under composition,

`O2 in Cl(A ∪ {O1})`.

Hence

`Cl(A ∪ {O2}) ⊆ Cl(A ∪ {O1})`.

Since `u,v` are units of `A`, their inverses `u^-1,v^-1` are also in `A`, and

`O1 = u^-1 ∘ O2 ∘ v^-1`.

Thus

`O1 in Cl(A ∪ {O2})`, giving

`Cl(A ∪ {O1}) ⊆ Cl(A ∪ {O2})`.

Therefore the closures are equal. QED.

## 4. Consequence — same-class re-acquisition is necessarily redundant

If a state has already admitted one representative `O1`, then admitting another `O2 ~_A O1` cannot enlarge composition closure.

This is not merely an empirical regularity from V104/V105. Under the stated assumptions it is forced algebraically.

The finite experiments test whether their proposed identity transformations really satisfy these assumptions in executable worlds.

## 5. Why invertibility is necessary

If arbitrary non-invertible maps in `A` are allowed to define identity, equality of generated closures need not follow.

A non-invertible coordinate map can erase information and map a genuinely stronger/new behaviour into an old one without allowing reconstruction in the opposite direction.

That is exactly the failure mode observed by the V104/V105 negative controls.

So the quotient relation should use **old-capability automorphisms/units**, not arbitrary old transformations.

This gives a principled reason for the empirical rule rather than a post-hoc restriction.

## 6. Capability reachability preorder

Let quotient classes be identified by old-capability orbit.

Define a relation on candidate classes:

`[O1]_A <=_A [O2]_A`

iff

`O1 in Cl(A ∪ {O2})`.

Equivalently, by the closure theorem, any representative of class `[O1]_A` becomes reachable after admitting any representative of `[O2]_A`.

### Well-definedness

The relation does not depend on which literal representative is chosen for either class.

For the right argument, if `O2' ~_A O2`, the theorem gives

`Cl(A ∪ {O2'}) = Cl(A ∪ {O2})`.

For the left argument, if `O1' ~_A O1` and `O1` is reachable, then composing with the old units witnessing `O1' ~_A O1` also makes `O1'` reachable.

Therefore `<=_A` is a relation on quotient classes, not syntax.

### Reflexivity

`[O]_A <=_A [O]_A` because `O in Cl(A ∪ {O})`.

### Transitivity

If

`[O1]_A <=_A [O2]_A`

and

`[O2]_A <=_A [O3]_A`,

then `O2` is constructible from `A ∪ {O3}`. Any finite composition expression constructing `O1` from `A ∪ {O2}` can therefore substitute the construction of `O2`, yielding `O1 in Cl(A ∪ {O3})`.

Hence

`[O1]_A <=_A [O3]_A`.

Thus `<=_A` is a **preorder**.

It becomes a partial order after quotienting again by mutual reachability:

`C1 ≡reach C2` iff `C1 <= C2` and `C2 <= C1`.

This is important: the empirical phrase “capability lattice” should not be promoted to a general theorem without proving joins/meets. The structure guaranteed here is a preorder, and a partial order after mutual-reachability quotienting.

## 7. Developmental event as a state change

The mathematically stable unit of acquisition is therefore not a literal operator token.

A candidate event can be represented by the closure transition

`A -> Cl(A ∪ {O})`.

Two candidate operators represent the same acquisition event whenever they induce the same closure transition; old-unit orbit equivalence is a sufficient condition for this equality.

This suggests two nested identity notions:

1. **coordinate identity**: `[O]_A` under old-capability units;
2. **developmental identity**: operators whose admission generates the same capability closure.

The second can be coarser than the first. Two operators not related by a simple old automorphism may still generate the same enlarged closure.

That is a new pressure-test target: determine whether empirical operator identity should ultimately be orbit identity or closure-extension identity.

## 8. Verifier index and refinement

The closure/order construction above concerns executable reachability.

Verifier authority `V` determines which behavioural distinctions are currently justified. Therefore the operational developmental state should combine both structures:

`D(A,V) = (Reachability(A), Pi(V))`.

Changes can then be classified as:

- **EXTEND**: `Cl(A ∪ {O})` strictly enlarges executable reachability;
- **REFINE**: stronger verifier authority splits an observational equivalence class without necessarily enlarging executable reachability;
- **COLLAPSE**: after capability growth, an earlier novelty distinction becomes reachable from the enlarged old state and is no longer novel relative to that state;
- **RETRACT**: governance removes or disables an admitted capability/scope after contradictory verifier evidence.

EXTEND and REFINE are mathematically distinct operations. This distinction explains why a new separator can change the quotient without constituting a new executable primitive.

## 9. Connection to current evidence

The theory predicts several already-observed bounded phenomena:

- V104/V105: literal representatives related by invertible old transformations have the same closure consequence, while non-invertible transforms create false collapse controls.
- V105: distinct quotient classes can have different closure sizes and directed reachability.
- V106B: literal repair identity can fail while quotient-level transport succeeds.
- V108: the relevant coordinate relation can be selected from verifier evidence rather than supplied by name.
- V109: the same induced relation transports a distinct repair family.
- V110: independently arising historical repairs can occupy recurrent quotient classes, though V112/V112B correctly show that the amount of retrospective recurrence is not statistically decisive by itself.
- V111: prospectively tests whether a quotient frozen on one corpus predicts repair structure in another corpus.

## 10. Stronger theoretical target exposed by this note

The old working claim was roughly:

> the new operator is an equivalence class modulo old-language transformations.

The sharper claim is:

> a developmental capability is identified by the change it induces in verifier-governed reachable behaviour; literal operators are representatives, old-unit orbits are presentation-invariant sufficient identity classes, and those classes themselves carry a reachability preorder.

This removes one avoidable researcher-choice dependence: changing coordinates inside the already available automorphism group cannot change the generated capability state.

It does **not** remove dependence on:
- the chosen old capability state `A`;
- the composition/type discipline;
- verifier authority `V`;
- resource bounds when closure is operationally bounded.

Those indices should remain explicit rather than being hidden under claims of absolute representation independence.

## 11. Next falsification

The most valuable next theory/experiment pair is now:

### Closure-extension identity test

Search for operators `O1,O2` such that:

- `O1` and `O2` are **not** in the same old-unit orbit;
- but `Cl(A ∪ {O1}) = Cl(A ∪ {O2})`.

If such examples recur, orbit identity is still too fine and the true developmental identity is the induced closure extension.

Conversely, find operators in different orbit classes whose closures differ sharply; these demonstrate why literal syntax is too fine but “all new things are equivalent” is too coarse.

GF(4)/GF(5) are immediate exact substrates for this test, followed by the natural-code repair grammar.

## Claim boundary

The closure/orbit theorem and preorder facts are deductive consequences of the stated algebraic assumptions. They do not establish that arbitrary reasoning systems possess a tractable composition-closed monoid, that their relevant automorphism group can always be discovered, or that natural conceptual growth is fully characterized by this construction.
