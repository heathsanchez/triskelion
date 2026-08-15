# V113 Closure-Extension Identity — Result

Protocol was frozen first in `protocols/V113_CLOSURE_EXTENSION_IDENTITY_PRECOMMIT.md`.

Experiment: `experiments/V113_CLOSURE_EXTENSION_IDENTITY.py`.

Primary execution was an exact local execution of the committed algorithm after protocol freeze. GitHub-hosted attestation remains to be added when runner capacity is available.

## Verdict

**PASS_IMPLEMENTATION_GATES**

Primary discovery:

**COARSER_THAN_ORBIT**

The stronger developmental identity is strictly coarser than old-unit orbit identity in GF(5).

## GF(4)

Exact unary world:

- non-affine literal candidates: **240**
- old-unit orbits: **4**
- exact developmental closure identities: **4**
- orbit sizes: `48, 36, 144, 12`
- closure sizes: `64, 52, 244, 28`

In GF(4), old-unit orbit identity is empirically tight: no two distinct orbits generate the same exact closure.

## GF(5)

Exact unary world:

- non-affine literal candidates: **3100**
- old-unit orbits: **12**
- exact developmental closure identities: **7**

Orbit sizes:

`100, 200, 400, 200, 400, 200, 200, 400, 400, 100, 400, 100`

Exact closure sizes by orbit:

`125, 225, 925, 925, 925, 925, 625, 3025, 3025, 625, 3025, 125`

But closure cardinality alone is not the identity criterion. Exact member sets reveal the following developmental equivalence groups:

- `{0}`
- `{1}`
- `{2,3}`
- `{4,5}`
- `{6,9}`
- `{7,8,10}`
- `{11}`

Therefore four separate multi-orbit collapses occur:

- old-unit orbits **2 and 3** generate exactly the same enlarged capability closure;
- orbits **4 and 5** generate exactly the same closure;
- orbits **6 and 9** generate exactly the same closure;
- orbits **7, 8 and 10** generate exactly the same closure.

These orbit pairs/groups are not merely equal in closure size; their **full exact generated closure sets are equal**.

So the converse of the orbit theorem fails:

`same old-unit orbit  =>  same generated closure`

is true, but

`same generated closure  =>  same old-unit orbit`

is false.

## Stronger identity object

The result supports a sharper developmental equivalence:

`O1 ≡dev O2  iff  Cl(A ∪ {O1}) = Cl(A ∪ {O2})`.

Old-unit orbit identity remains a useful presentation-invariant sufficient condition, but it is not the maximally compressed identity of a capability acquisition event.

For GF(5), the compression hierarchy is:

`3100 literal operators -> 12 coordinate orbits -> 7 developmental closure identities`.

Thus the object that matters for future capability is more naturally **the state transition induced by acquisition** than the representative operator or even its coordinate orbit.

## Closure size is not enough

V113 also found distinct exact developmental closures with identical cardinality.

Examples:

- orbit 0 and orbit 11 both have closure size **125**, but the exact closure sets differ;
- orbit groups `{2,3}` and `{4,5}` all have closure size **925**, but the two developmental closures differ.

Therefore a scalar measure such as closure size cannot identify capability state.

The state must preserve which behaviours are reachable, not merely how many.

## Mutual reachability

Across both GF(4) and GF(5), exact closure equality agreed perfectly with mutual reachability between orbit representatives:

`f in Cl(A+g)` and `g in Cl(A+f)`

iff their exact generated closures were equal.

No mismatches occurred.

This supports the quotient-of-preorder construction in `theory/CAPABILITY_ORBIT_PREORDER.md`:

- old-unit quotient removes coordinate/presentation redundancy;
- reachability gives a preorder;
- quotienting by mutual reachability gives developmental identity classes / a partial-order-level capability structure.

## Interpretation

This materially sharpens the quotient idea.

The earlier working unit was:

`new capability = [O]_(A,V)` modulo old invertible coordinate changes.

V113 shows that this can still over-count acquisition events. Two coordinate-inequivalent operators can nevertheless have exactly the same developmental consequence because either one generates the same future capability state.

The more general unit is therefore:

`developmental identity = induced verified closure extension`.

A literal operator is a representative; an old-unit orbit is a presentation-invariant sufficient class; the actual acquisition event is the change in reachable capability state.

## Claim boundary

Exact unary GF(4)/GF(5) function monoids only. This is a mathematical/finite structural result, not yet evidence that natural code or open-ended reasoning systems admit tractable exact closure-extension identities.
