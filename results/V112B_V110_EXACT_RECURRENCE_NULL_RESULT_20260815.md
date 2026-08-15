# V112B Exact V110 Recurrence Null Audit

This is a deterministic post-V112 audit, not a prospectively frozen new scientific test.

The V112 Monte Carlo null preserved the three repaired programs and their exact observed pass counts, then randomized only which candidate identities were successful. V112 estimated the recurrence event at about 0.092.

V112B removes Monte Carlo error by exactly enumerating the same conditional event through compressed combinatorial states.

## Conditioning

Observed passing-repair counts from V110:

- knapsack: 2 successes among 11 comparator candidates
- next_permutation: 4 among 22
- quicksort: 4 among 22

Event:

`recurrent_count >= 2 AND diverse_recurrent_count >= 2`

where recurrence requires the same quotient class in at least two programs and diversity requires at least two literal repair signatures within that recurrent quotient class.

## Exact result

Total equally weighted candidate-success configurations under the conditional null:

**2,943,007,375**

Configurations satisfying the V110-level event:

**268,919,980**

Therefore

`P(event | V112 conditional null) = 268,919,980 / 2,943,007,375`

= **0.09137591101007689**.

So the V112 negative conclusion is unchanged and now exact:

**0.09138 > 0.05**.

## Interpretation

This does not invalidate V110's causal repair evidence. It says only that, conditional on exactly these three repaired programs and their observed numbers of passing comparator candidates, the amount of quotient recurrence seen in V110 is not by itself rare enough under identity randomization to support a conventional 0.05 significance claim.

That strengthens the reason for V111: the next important evidence should be prospective cross-corpus prediction rather than extracting more significance from the same QuixBugs repair set.

This remains a conditional post-selection audit, not a population-level p-value over software bugs.
