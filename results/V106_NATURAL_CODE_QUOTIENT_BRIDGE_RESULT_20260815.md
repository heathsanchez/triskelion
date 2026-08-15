# V106 Natural-Code Quotient Bridge — Result

Frozen protocol: `protocols/V106_NATURAL_CODE_QUOTIENT_BRIDGE_PRECOMMIT.md`

Hosted run: `31868175128`

Hosted job: `94972409678`

Head: `e80e241ba1ea34230ff0c84251c3759898373053`

Artifact: `9242642299`, digest `sha256:91339b8dec0292ef1c43f737d6f5113f2b7b23b9d9ac732223aaf3db50a43f86`

## Verdict

**MIXED / FAIL_V106_NATURAL_CODE_QUOTIENT_BRIDGE**

The scientific failure is narrow and informative: **G1 failed because the precommitted hash split produced only one qualified held-out program**, below the required minimum of two held-out programs.

This must not be promoted to a PASS.

## What did pass

Qualification itself was stronger than the split failure suggests:

- **13** qualified causal mutation/repair tasks;
- **8** distinct externally authored QuixBugs programs;
- unchanged upstream tests;
- **12** acquisition tasks across 7 programs;
- **1** held-out task from `quicksort`.

All other frozen gates passed:

- G2 presentation invariance: PASS;
- G3 controlled mutation causal in both LT/GT presentations: PASS;
- G4 quotient retention beats literal identity on the available held-out task: PASS (`0/1` literal vs `1/1` quotient);
- G5 ablation restores failure: PASS (`1/1`);
- G6 both literal representatives repair the same external task semantics: PASS;
- G7 no source-file leakage: PASS;
- G8 negative identity control reported: PASS.

Qualified programs were:

`find_in_sorted, hanoi, is_valid_parenthesization, kth, mergesort, pascal, quicksort, sieve`.

## Important negative

The failure was **not** that the quotient relation broke on natural code. The supplied `DUAL_CMP` relation survived every qualified natural-code site tested. The failure was that the prospectively chosen single hash split happened to allocate seven of eight qualifying programs to acquisition and only one to held-out.

That is still a real protocol failure: the planned source-distinct evidence floor was not met, so the headline bridge claim is not admitted from V106.

## Correct next test

Do not choose a friendlier single split after seeing V106.

The clean follow-up is **leave-one-qualified-program-out evaluation** under the same qualification procedure. Every qualifying program must serve as held-out in turn, with all other qualifying programs as acquisition. This removes dependence on one arbitrary split and makes the source-distinct criterion strictly harder: the quotient identity must transfer to every qualifying source family, not merely a selected partition.

That follow-up should be frozen as a new experiment (`V106B`) and V106 must remain recorded as MIXED.

## Claim boundary

Controlled mutation on correct external QuixBugs Python code, not historical-bug repair or natural quotient discovery. The quotient relation was supplied. V106 itself is not a PASS.
