# V94 Dynamic State Invariants — Attested Result

Status: **MIXED / REACHABILITY NEGATIVE**

Primary workflow run: `31790728003`

Artifact: `9215561586` (`v94-dynamic-state-invariants`)

Artifact SHA-256: `c9d972a88de12c7c9af64ac33ec3c894f1a6d98a4fc1f1ab40dfdeffc223a4c3`

Primary verdict: `MIXED_DYNAMIC_STATE_INVARIANTS_V94`

## Result

Seven nonzero training-side dynamic prototypes were induced from independently authored correct behavior. However on all eight held-out tasks the frozen generic mutation substrate contained **zero successful candidate**:

- `next_palindrome`
- `kth`
- `hanoi`
- `sieve`
- `next_permutation`
- `reverse_linked_list`
- `to_base`
- `shortest_path_lengths`

Thus:

- unrestricted reachable success = 0/8
- learned dynamic ranking success = 0/8
- coordinate-null ranking success = 0/8

The learned arm often assigned high similarity to candidate dynamic deltas, but because no candidate was correct this does not test transfer usefulness.

## Binding interpretation

V94 is primarily a **constructor reachability failure**, not evidence against dynamic state-transition structure.

A ranking/ontology claim is uninterpretable when the fixed constructor substrate contains no successful held-out candidate. Future ranking tests must hold a richer constructor K fixed across all arms and establish a nonzero reachability ceiling before asking whether learned structure reduces search.

Also, V94 executed every candidate through the full test suite to obtain dynamic traces. Therefore V94 cannot support an economic claim about reducing expensive verification even if a ranking difference had appeared. V97+ separates a cheap probe channel from the protected full verifier.
