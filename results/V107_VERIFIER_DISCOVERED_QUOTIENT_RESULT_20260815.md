# V107 Verifier-Discovered Natural-Code Quotient Relation

Protocol: `protocols/V107_VERIFIER_DISCOVERED_QUOTIENT_PRECOMMIT.md`

Successful hosted run: **31868886967**

Head: `819504634b2bf66aa037c391d030354c01f3bead`

Artifact: `v107-verifier-discovered-quotient`

Artifact digest: `sha256:18d82eed34b08c8da9742e9d3e87afcf93dc520c067afab59032ddf48d65c180`

Primary verdict: **PASS_V107_VERIFIER_DISCOVERED_QUOTIENT**

## Harness note

An earlier hosted execution failed because rapid same-size Python source rewrites could reuse stale bytecode from `__pycache__`, contaminating candidate verification. The frozen scientific protocol and candidate family were unchanged. The harness was repaired to purge bytecode caches and invoke Python with `-B`; the corrected hosted run then executed the frozen gates successfully.

The failed run remains visible as a harness negative rather than being erased.

## Natural qualification

Same externally authored QuixBugs corpus and causal qualification as V106B, pinned at:

`4257f44b0ff1181dedaedee6a447e133219fcebf`

Qualified:

- **13 tasks**
- **8 programs**
- `find_in_sorted`
- `hanoi`
- `is_valid_parenthesization`
- `kth`
- `mergesort`
- `pascal`
- `quicksort`
- `sieve`

## Relation discovery

The specific quotient relation was not supplied to the selector. Each leave-one-program-out fold selected from the frozen nonidentity invertible family:

- `SWAP_ONLY`
- `FLIP_ONLY`
- `SWAP_AND_FLIP`

Selection used only unchanged upstream verifier outcomes on acquisition programs.

Every fold selected **SWAP_AND_FLIP uniquely and perfectly**.

Fold scores:

| held-out program | acquisition tasks | SWAP_ONLY | FLIP_ONLY | SWAP_AND_FLIP | selected |
|---|---:|---:|---:|---:|---|
| find_in_sorted | 11 | 0 | 0 | **11** | SWAP_AND_FLIP |
| hanoi | 12 | 0 | 0 | **12** | SWAP_AND_FLIP |
| is_valid_parenthesization | 12 | 0 | 0 | **12** | SWAP_AND_FLIP |
| kth | 10 | 0 | 0 | **10** | SWAP_AND_FLIP |
| mergesort | 11 | 0 | 0 | **11** | SWAP_AND_FLIP |
| pascal | 11 | 0 | 0 | **11** | SWAP_AND_FLIP |
| quicksort | 12 | 0 | 0 | **12** | SWAP_AND_FLIP |
| sieve | 12 | 0 | 0 | **12** | SWAP_AND_FLIP |

Thus the two alternative invertible source transformations were rejected by the acquisition verifiers in every fold, while the same relation was independently recovered without held-out evidence.

## Transfer

On held-out GT-presentation relaxed tasks:

- literal acquisition repair `LE_TO_LT`: **0/13**
- repair transported through the verifier-selected relation: **13/13**
- ablation restored the relaxed failure: **13/13**

All 9 frozen gates passed:

- G1 natural qualification — PASS
- G2 fold coverage — PASS
- G3 relation discovery — PASS
- G4 relation consistency — PASS
- G5 literal baseline failure — PASS
- G6 discovered quotient transfer — PASS
- G7 causal ablation — PASS
- G8 held-out independence — PASS
- G9 negative controls — PASS

## Allowed claim

> Across leave-one-program-out folds on externally authored QuixBugs Python programs, a specific invertible comparison-coordinate relation was selected solely from acquisition-program verifier evidence within a frozen three-template family, then used to transport a retained repair across source presentation change where literal retention failed.

## Boundary

This is stronger than V106B because the specific relation is verifier-selected rather than supplied. It is still **not arbitrary relation invention**: the three-template invertible comparison meta-family was supplied. It is not historical bug repair and does not yet establish a natural-code capability lattice.
