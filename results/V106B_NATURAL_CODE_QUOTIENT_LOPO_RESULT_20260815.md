# V106B Natural-Code Quotient LOPO — Result

Frozen protocol: `protocols/V106B_NATURAL_CODE_QUOTIENT_LOPO_PRECOMMIT.md`

Hosted run: `31868318892`

Hosted job: `94972749471`

Head: `3ba09f2ecb026db267372e27be9819faa5e56ee7`

Artifact: `9242679541`

Artifact digest: `sha256:dd1d2b740daa1782617f45070e9d74e1e44c4dcd97b02c2beaac0fc5cf6b7e93`

## Verdict

**PASS_V106B_NATURAL_CODE_QUOTIENT_LOPO**

All nine frozen gates passed.

## Qualification

The V106 qualification procedure was recomputed from the pinned external corpus rather than hard-coding V106's task list.

It again produced:

- **13** qualified causal tasks;
- **8** distinct externally authored QuixBugs programs:
  - `find_in_sorted`
  - `hanoi`
  - `is_valid_parenthesization`
  - `kth`
  - `mergesort`
  - `pascal`
  - `quicksort`
  - `sieve`

For every qualified task:
- canonical-LT and canonical-GT unmutated presentations both passed the unchanged upstream tests;
- relaxing the strict comparison caused both presentations to fail;
- tightening the comparison repaired both presentations.

## Leave-one-program-out result

Every qualifying program served as the sole held-out source family once.

Eight folds, all passed:

| held-out program | held-out tasks | literal solves | quotient solves | ablation failures |
|---|---:|---:|---:|---:|
| find_in_sorted | 2 | 0 | 2 | 2 |
| hanoi | 1 | 0 | 1 | 1 |
| is_valid_parenthesization | 1 | 0 | 1 | 1 |
| kth | 3 | 0 | 3 | 3 |
| mergesort | 2 | 0 | 2 | 2 |
| pascal | 2 | 0 | 2 | 2 |
| quicksort | 1 | 0 | 1 | 1 |
| sieve | 1 | 0 | 1 | 1 |

Aggregate over all held-out appearances:

- literal retained `LE_TO_LT`: **0/13**;
- quotient retained `TIGHTEN_STRICT`, instantiated in held-out GT coordinates as `GE_TO_GT`: **13/13**;
- repair ablation restored the failing relaxed state: **13/13**.

No source program appeared in both acquisition and held-out within any fold.

## Interpretation

This repairs V106's one-shot split-coverage failure without rewriting V106: V106 remains MIXED, while V106B asks a harder source-distinct question in which **every** qualifying source family must transfer.

Exact allowed wording:

> Across all eight qualifying source families in this controlled natural-code bridge, a strict-bound repair represented as a quotient class under the supplied invertible comparison-dualization relation transferred across every leave-one-program-out source-distinct coordinate shift (13/13), while retaining the acquisition literal repair token alone transferred on 0/13; targeted ablation restored failure on 13/13.

## Claim boundary

The code and tests are external/natural, but the mutation family and `DUAL_CMP` quotient relation are supplied. This is not natural discovery of the quotient relation, historical bug repair, autonomous operator invention, or a natural-code lattice result.
