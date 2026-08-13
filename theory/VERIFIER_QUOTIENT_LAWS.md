# Verifier-Indexed Quotient Laws

## Setup

Let `X` be a set of candidate capabilities, programs, proofs, operators, or representations. Let a verifier authority `V` be a set of observations/tests. Each observation `v in V` returns an observable signature for each candidate.

Define verifier-indexed observational equivalence:

`x ~_V y` iff `obs_v(x) = obs_v(y)` for every `v in V`.

Let `Pi(V)` be the partition of `X` into equivalence classes under `~_V`.

## Law 1 — Equivalence

For fixed `V`, `~_V` is reflexive, symmetric, and transitive, hence an equivalence relation.

## Law 2 — Authority monotonicity / partition refinement

If `V0` is a subset of `V1`, then:

`x ~_(V1) y  =>  x ~_(V0) y`.

Equivalently, `Pi(V1)` refines `Pi(V0)`.

Adding observational authority may split an old class, but cannot merge candidates that the weaker authority already distinguished.

Proof: equality on every observation in `V1` implies equality on the subset `V0`.

## Law 3 — Reversibility by provenance

If an old class under `V0` split only because of observations in `V1 \ V0`, then removing those observations restores the old `V0` equivalence. Therefore a Lawbook should retain class members and verifier provenance rather than destructively replacing a coarse class by a finer representative.

## Law 4 — Minimal separator

For `x ~_V y`, any observation `s` with `obs_s(x) != obs_s(y)` is a separator. Adding one such separator is sufficient to split `x` and `y` in `Pi(V union {s})`.

For larger classes, the minimal refinement problem is to choose a minimum-cost observation set whose signatures induce the capability distinctions required by the downstream task.

## Law 5 — Closure and quotient interact

Search should operate over `Closure(A) / ~_V`, not raw syntax, when the quotient law is valid for the current verifier and scope. If authority later grows, the quotient must be refinable without losing the underlying candidates or provenance.

## External evidence checkpoint

The V45–V66 fixed QuixBugs sequence provides external executable examples under one frozen weak/protected protocol:

- 22 targets total.
- 19 targets: weak authority already distinguished buggy/correct, so no quotient was admitted.
- 3 targets: V54 `is_valid_parenthesization`, V57 `next_palindrome`, V66 `lis` were genuinely equivalent under weak authority and split under protected authority.
- All three positive cases satisfy reversibility: removing protected authority restores the weak quotient.

Sequence ledger: `results/V45_V66_LEDGER.txt`.
Full V51–V66 schedule precommit: `890866b10d03ef47abaebdd743aa7b392c68313a`.

## Architectural consequence

Lawbook equality should be represented as a scoped, verifier-indexed judgment such as:

`Equivalent(x, y | verifier=V, scope=S, evidence=E)`

rather than permanent global identity.

The algebra is therefore naturally a family of quotients indexed by observational authority. As authority grows, the family moves monotonically toward finer partitions while preserving the ability to reconstruct earlier coarser quotients.

## Claim boundary

Laws 1–4 follow from the definition of observational equivalence and do not depend on the empirical experiments. The external experiments demonstrate that the refinement event occurs nontrivially on independently authored executable software under a frozen protocol; they do not establish autonomous discovery of arbitrary separators.