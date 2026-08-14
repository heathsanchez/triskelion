# V100 balanced-K diagnostics — 2026-08-14

These are explicitly **NONCLAIM diagnostics**. They are recorded because they identify constructor-language confounds and determine the next frozen tests; they are not scientific PASS evidence for dynamic organs.

## V100K — static constructor coverage audit

- branch: `v100k-constructor-coverage-audit`
- run: `31793496441`
- artifact: `9216418827`
- artifact digest: `sha256:1d3bb3714c2a77e964d4f0e76eb1c4308055b2806b75817d07b779714192dbe6`
- external corpus: frozen QuixBugs
- status: `NONCLAIM_DIAGNOSTIC_ONLY`

The audit compares the effective mutation-family coverage under the old ordered cap against the balanced cap, without using verifier outcomes.

Across 40 programs:

- mean represented families, ordered K: `3.925`
- mean represented families, balanced K: `5.225`
- tasks where balancing exposes additional families: `10/40`
- tasks with unchanged family count: `30/40`

Several cap-saturated programs were effectively reduced to `NAME_SUB` only under the old constructor despite later mutation families existing in the supplied language. Examples:

- `knapsack`: 1 family -> 7
- `kth`: 1 -> 7
- `lis`: 1 -> 8
- `mergesort`: 1 -> 8
- `minimum_spanning_tree`: 1 -> 5
- `next_permutation`: 1 -> 6
- `shortest_path_length`: 1 -> 9

Binding interpretation: the earlier globally capped rich constructor had a real family-order truncation confound. V100 therefore tests a materially broader **effective** K even though the nominal family inventory is unchanged.

## V100P — shortened balanced-K source-distinct preflight

- branch: `v100p-balanced-k-preflight`
- run: `31793309945`
- artifact: `9216630872`
- artifact digest: `sha256:af4f971e05b3f7fd9059fec73eb1d588ca219838e47f5b02516891b2b763b9a1`
- status: `NONCLAIM_DIAGNOSTIC_ONLY`

Frozen shortened split:

Training:
- `mergesort`
- `longest_common_subsequence`
- `quicksort`
- `levenshtein`

Held out:
- `breadth_first_search`
- `sieve`
- `subsequences`
- `find_in_sorted`

Training verifier-improving candidates:

- `mergesort`: 2 improving candidates (`CONST_SUB`, `NAME_SUB`), best failing-test gain 12
- `longest_common_subsequence`: 0
- `quicksort`: 1 (`CMP_OP`), gain 1
- `levenshtein`: 1 (`CONST_SUB`), gain 5

The source-distinct dynamic admission rule produced one component supported by two distinct source programs:

`{mergesort, levenshtein}`

with medoid mutation family `CONST_SUB`.

This is the first useful shift relative to V97: balanced K no longer starves the training side. A verifier-induced source-distinct dynamic component can form without reading correct implementations.

However, the held-out candidate language had zero solution reachability on all four tasks:

- `breadth_first_search`: unreachable
- `sieve`: unreachable
- `subsequences`: unreachable
- `find_in_sorted`: unreachable

Therefore learned, coordinate-null and hash ranking arms all solved zero. Ranking/organ utility is not interpretable on this prefix.

Binding interpretation:

`balanced K -> training improvements -> source-distinct dynamic component`

is observed diagnostically, but

`balanced depth-1 K -> held-out reachable repair`

is still false on this prefix.

The next test is closure-before-invention: V101P checks bounded depth-2 composition of the exact same balanced generic families. If depth 2 remains unreachable, the evidence for genuine constructor-language inadequacy becomes stronger; if depth 2 succeeds, the obstruction was compositional depth rather than missing primitive families.
