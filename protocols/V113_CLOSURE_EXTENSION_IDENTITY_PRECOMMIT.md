# V113 Closure-Extension Identity — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen before inspecting V113 GF(4)/GF(5) closure-equivalence results.

## Question

Is old-unit orbit identity still too fine for developmental capability identity?

The deductive note `theory/CAPABILITY_ORBIT_PREORDER.md` proves that operators in the same old-unit orbit generate the same enlarged closure. The converse need not hold.

V113 asks whether distinct old-unit orbits can nevertheless induce the **same capability closure extension**.

If yes, the stronger developmental identity is not literal operator identity and not necessarily old-unit orbit identity, but the induced closure state:

`O1 ≡dev O2  iff  Cl(A ∪ {O1}) = Cl(A ∪ {O2})`.

## Frozen substrates

Use the exact unary finite-function worlds already specified independently in V105/exploratory follow-up:

1. GF(4): all `4^4 = 256` unary functions; old capability all affine maps `x -> ax+b`; old coordinate identity group affine bijections.
2. GF(5): all `5^5 = 3125` unary functions; old capability all affine maps `x -> ax+b`; old coordinate identity group affine bijections.

No new candidate restriction is allowed after results are inspected.

## Exact objects

For every non-affine unary function `f`:

- compute its old-unit orbit under affine-bijection pre/post composition;
- compute exact composition closure `Cl(A ∪ {f})`;
- assign an exact closure identity by the full sorted member set, not closure size alone.

Define:

- `orbit_id(f)` = old-coordinate orbit;
- `dev_id(f)` = exact generated closure set.

## Frozen gates

### G1 — theorem check
Within every old-unit orbit, every representative must have the same exact `dev_id`. Failure falsifies the implementation/assumptions.

### G2 — converse test
Report whether there exist distinct old-unit orbits with identical exact `dev_id`.

This is a discovery gate, not forced PASS. Two legitimate outcomes:
- `COARSER_THAN_ORBIT`: at least one distinct-orbit pair shares exact closure;
- `ORBIT_TIGHT_IN_TESTED_WORLDS`: no such pair in either substrate.

### G3 — consequence diversity
There must exist at least two distinct developmental closure identities among non-affine candidates in GF(4) or GF(5). Otherwise the test substrate is too degenerate to discriminate developmental identity.

### G4 — closure size is insufficient identity if witnessed
Search for two distinct exact developmental closures with the same cardinality. If found, report them. This tests whether using only closure size would falsely merge capabilities.

### G5 — reachability quotient compression
For each substrate report:
- number of literal non-affine operators;
- number of old-unit orbits;
- number of exact developmental closure identities;
- compression ratios literal -> orbit -> developmental identity.

### G6 — mutual reachability correspondence
For each pair of old-unit orbits, test whether equal exact closure is equivalent to mutual reachability of representatives over the same old state:

`f in Cl(A+g)` and `g in Cl(A+f)`.

Under exact composition closure these should coincide with closure equality. Any discrepancy is a bug or a counterexample to the proposed implementation-level relation.

## Primary interpretation

V113 does not require the developmental partition to be strictly coarser than the orbit partition. Its purpose is to decide that question exactly in two finite substrates.

If distinct orbits share closures, promote closure-extension identity as the stronger mathematical unit.

If they do not, retain orbit identity as empirically tight in these substrates while keeping closure-extension identity as the more general definition.

## Claim boundary

Finite unary function monoids only. No claim about natural code or arbitrary reasoning systems follows directly.
