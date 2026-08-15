# V108 Generic Verifier-Induced Quotient Relation

Hosted run: **31869147260**

Head: `db54cb1ee29cae5644a03d9f50068b8bcd7c04a0`

Artifact: `v108-generic-verifier-quotient`

Digest: `sha256:e188a84ac90eac13ede163cd6aaa42ea38023f7da22fd0d6a084119e298848ee`

Verdict: **PASS_V108_GENERIC_VERIFIER_QUOTIENT_INDUCTION**

## What changed from V107

V107 selected from three explicitly named invertible templates. V108 removed those names and widened selection to a generic local comparison grammar:

- operand coordinate: KEEP or SWAP;
- target comparator token: `<`, `>`, `<=`, `>=`, `==`, `!=`;
- strict and relaxed target tokens distinct;
- literal identity excluded.

This produced exactly **59 nonidentity candidate relations**.

Candidates were scored using acquisition-only upstream verifier behavior. A candidate had to make the transformed strict program pass and make the transformed relaxed program reproduce the **exact same failing pytest node-ID set** as the canonical relaxed mutation on every acquisition task.

## Data

Frozen natural task set inherited from the prior hosted V106B qualification:

- **13 tasks**
- **8 programs**: find_in_sorted, hanoi, is_valid_parenthesization, kth, mergesort, pascal, quicksort, sieve.

Evaluation: leave one whole program out.

## Fold-local induction

Every fold had exactly **one** perfect candidate out of 59:

`SWAP:>|>=`

That relation was independently induced in all eight folds.

The remaining **58/59 = 98.305%** candidates were rejected in every fold.

Representative fold scores:

- hold out find_in_sorted: winner 11/11; next-best candidates 6/11;
- hold out hanoi: winner 12/12; next-best 6/12;
- hold out kth: winner 10/10; next-best 7/10;
- hold out quicksort: winner 12/12; next-best 7/12.

No held-out result was used for selection.

## Transfer

On held-out target-presentation tasks:

- literal acquisition repair with no coordinate transport: **0/13**;
- repair transported through the induced relation: **13/13**;
- ablation restored failure: **13/13**.

All 10 frozen gates passed, including generic-space size, unique induction, cross-fold stability, >90% candidate rejection, held-out independence, representative correctness and causal ablation.

## Allowed claim

> On source-distinct externally authored QuixBugs programs, a repair-transport quotient relation was induced uniquely from acquisition verifier behavior within a generic 59-relation comparison-edit grammar, then transferred causally to held-out programs where literal repair identity failed.

## Boundary

The AST edit grammar is still supplied. V108 is not arbitrary transformation invention, historical bug repair, or representation-independent ontology discovery. Its contribution is that the *specific* relation and its repair transport are no longer supplied or named in the candidate set; they are selected by external verifier evidence.
