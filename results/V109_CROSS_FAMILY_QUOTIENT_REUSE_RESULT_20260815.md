# V109 Cross-Family Quotient Reuse — Result

Protocol: `protocols/V109_CROSS_FAMILY_QUOTIENT_REUSE_PRECOMMIT.md`

Hosted run: **31869268153**

Head: `3f323a199d686f4232d790d199b18f4a36fa31c6`

Artifact: `v109-cross-family-quotient-reuse`

Artifact id: `9242957963`

Artifact digest: `sha256:4798e5dd433d15582d8eab76a4488ce3f33d3ce0907c7e0596a6b9ba9bc96a14`

## Verdict

**PASS_V109_CROSS_FAMILY_QUOTIENT_REUSE**

All eight frozen gates passed.

## Question

Does the quotient relation learned from one repair family remain useful for a distinct repair/mutation family, or is it merely a compact restatement of the original `< -> <=` task?

## Family A — relation induction only

Family A uses the original strict-bound relaxation evidence:

- source mutation: `< -> <=`
- source repair: `<= -> <`

The relation is induced only from Family-A acquisition evidence inside the generic 59-pair grammar. In every LOPO fold the unique relation remains:

`SWAP:>|>=`

Family-B outcomes do not participate in relation selection.

## Protected Family B — distinct mutation/repair family

Family B is strict-order reversal rather than boundary relaxation:

- source-canonical correct: `KEEP:<`
- source mutation: `KEEP:>`
- source repair: `> -> <`
- quotient-transported target correct coordinate: `SWAP:>`
- quotient-transported target mutation: `SWAP:<`

So this is not the same token transition as Family A.

Protected Family-B qualification produced:

- **13 tasks**
- **8 programs**: `find_in_sorted`, `hanoi`, `is_valid_parenthesization`, `kth`, `mergesort`, `pascal`, `quicksort`, `sieve`

For every protected task, source and target mutations produced the same unchanged-upstream-test failure signature.

## Result

Across all protected Family-B held-out appearances:

- literal Family-B identity without quotient transport: **0/13**;
- quotient reuse using the relation induced only from Family A: **13/13**;
- target-mutation ablation remained failing: **13/13**.

Every source program was held out once; its evidence was absent from acquisition relation selection in that fold.

## Why this matters

V108 showed that the relation itself can be induced from verifier behavior rather than supplied by name. This result shows that the induced relation is not only useful for transporting the exact repair transition that identified it: it also transports a distinct strict-order-reversal repair family under the frozen protocol.

That is evidence for a reusable coordinate relation rather than a one-repair alias.

## Exact allowed claim

> In the controlled QuixBugs setting, the quotient relation induced exclusively from one causal repair family was reused without Family-B selection evidence to transport a distinct repair family across all 13 protected source-distinct tasks; literal identity solved 0/13 and ablation restored failure on 13/13.

## Boundary

The generic comparison AST grammar and both controlled mutation families are supplied. This is not arbitrary transformation invention, historical bug repair, or unrestricted cross-domain transfer.
