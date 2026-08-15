# V112 Conditional Recurrence Null for V110 — Result

Protocol: `protocols/V112_V110_RECURRENCE_NULL_PRECOMMIT.md`

## Verdict

**NOT SIGNIFICANT UNDER THE FROZEN CONDITIONAL NULL**

The exact committed V112 randomization algorithm was reproduced locally after the protocol was frozen, using the pinned V110 QuixBugs sources. GitHub Actions execution is queued at time of this result note, so this is not yet hosted-attested.

## Frozen setup

Observed V110 passing-candidate counts were preserved:

- `knapsack`: 2 passing candidates from 11 tested candidate identities;
- `next_permutation`: 4 from 22;
- `quicksort`: 4 from 22.

Source comparison-site structure was reconstructed from the pinned buggy sources:

- `knapsack`: one `<` site;
- `next_permutation`: two `<` sites;
- `quicksort`: one `<` and one `>` site.

For each of 200,000 deterministic randomization trials, V112 sampled the observed number of successes uniformly without replacement from each program's frozen candidate universe, then applied the unchanged V110 quotient map.

Primary event:

- at least two quotient classes recur across at least two distinct repaired programs; AND
- at least two recurrent classes have at least two distinct literal signatures.

This matches or exceeds the structural recurrence count observed in V110.

## Result

- trials: **200,000**
- frozen seed: **11220260815**
- null trials meeting/exceeding V110 event: **18,391**
- raw null frequency: **0.091955**
- plus-one Monte Carlo p-value: **0.0919595**

Therefore:

`p = 0.09196 > 0.05`

Under this particular conditional identity-randomization null, V110's two diverse recurrent classes are **not statistically exceptional at the frozen 0.05 threshold**.

## Interpretation

This is a useful negative result and should remain attached to V110.

It does **not** undo V110's causal facts:

- the primary search was blind to correct implementations;
- 10 actual one-site repairs passed the upstream verifier;
- ablation restored failure;
- literal variants collapsed into recurrent quotient classes across distinct historical programs.

But it means we should **not** use V110 alone to claim that the amount of recurrence is statistically surprising once we condition on the three repaired programs, their success counts, and their search geometry.

The stronger discriminator is therefore prospective prediction on a fresh corpus, not retrospective significance mining inside QuixBugs. That is exactly what V111 freezes before BugsInPy target execution.

## Claim boundary

V112 is post-V110 and conditional on V110's repaired programs/pass counts. It is not a population-level p-value. No alternate statistic or threshold is substituted after seeing this result.
