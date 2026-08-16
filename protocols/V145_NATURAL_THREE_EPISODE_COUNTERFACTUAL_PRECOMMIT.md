# V145 — Natural Three-Episode Developmental Counterfactual

## Status

**PRECOMMITTED — DO NOT ALTER AFTER ANY V145 ARM EXECUTES**

This protocol is governed by `DEVELOPMENTAL_CONTROLLER_CONSTITUTION_V1.md`. It tests a prospective natural three-generation developmental claim. It does not alter prior evidence or upgrade earlier bounded results.

## Scientific question

Does a frozen verifier-governed developmental procedure cause a genuine three-episode acquisition chain in which earlier verified acquisition changes what can be acquired later?

The target claim is not merely that retained operators are useful. The target is:

`E1 -> O1 -> changed reachable discovery state -> E2 -> O2 -> changed reachable discovery state -> E3 -> O3`

with causal ancestor ablations and matched controls.

## Frozen natural episode sequence

The episode order is fixed and may not be changed after execution begins:

1. `E1 = httpie/5`
2. `E2 = youtube-dl/32`
3. `E3 = pandas/66`

All three are pre-existing BugsInPy tasks from the frozen 501-bug / 17-project corpus lineage. E3 was admitted only after a fixed-commit-pass / buggy-commit-fail qualification under the historical runtime, with deterministic frozen ordering and no semantic skipping.

The authoritative corpus lock inherited from the CP3 lineage is:

`760b73f87bbe79b76c970c1b2ac4cdd83e5eb18ee3f4b9f2304a915fddbbd5ad`

The E3 qualification runtime is Python `3.8.3` as established by the eligibility experiment. Any inability to reproduce the required runtime, commits, native tests, or verifier is an infrastructure result, not a semantic failure.

## Frozen developmental procedure

Every arm receives the same base model/checkpoint, allowed source/test evidence, proposal mechanism, candidate language, verifier interface, call/token/candidate budget, seed policy, stopping rule, runtime, and episode order.

Only the developmental-state intervention differs by arm.

The controller must execute, for each episode:

`state -> residual -> old-closure test -> proposal -> verifier -> admit/reject -> state update`

A locally successful patch is not automatically an admitted operator. Promotion follows the already frozen controller rules and verifier boundary.

No arm may inspect fixed/reference implementations, developer patches, protected solution text, or future-episode semantic outcomes before that information is permitted by the parent protocol.

## Six frozen arms

### A — COLD

- Run E1, E2, E3 with no persistent promoted developmental state between episodes.
- Episode-local working memory may exist only inside the frozen per-episode budget.
- All promoted operators/laws are discarded before the next episode.

Purpose: baseline natural acquisition without developmental inheritance.

### B — O1_ONLY

- Run E1 normally and allow verified O1 promotion.
- Carry O1 into E2.
- At the E2 boundary, record all discoveries normally but block promotion of any new O2-like state before E3.
- Carry only the exact E1-admitted state into E3.

Purpose: test whether O1 alone is sufficient for the third episode and separate two-generation from three-generation effects.

### C — FULL

- Run the exact frozen controller normally through E1 -> E2 -> E3.
- Verified state admitted at E1 may affect E2.
- Verified state admitted at E2 may affect E3.
- No manual injection of target operators is allowed.

Purpose: candidate natural developmental chain.

### D — ANCESTOR_MINUS

- Execute E1 normally but prevent the verified E1 operator/capability from being promoted into persistent state.
- Do not replace it with a manually supplied O1.
- Run the same controller normally at E2 and E3 from the resulting counterfactual state.

Purpose: test whether the first ancestor is causally required for later natural acquisition.

### E — SHAM

- At the E1 and E2 promotion boundaries, retain deterministic inert objects matched as closely as practical for serialized size, field structure, and retrieval visibility, but incapable of changing executable proposal/closure/verifier behavior.
- Do not encode semantic hints, operator names, repair content, target identifiers, or future outcomes in sham objects.

Purpose: control for more state, more tokens, and persistence machinery alone.

### F — ORACLE_O2

- Do not run a developmental E1 -> E2 acquisition history.
- Before E3, inject only the exact explicit O2 artifact that was frozen from an independent eligible developmental lineage, using the same serialization and invocation pathway as FULL.
- Do not inject hidden trajectory records, residual traces, model deltas, caches, or additional state from the FULL history.

Purpose: distinguish `O2 is sufficient for E3` from `the developmental trajectory that produced O2 contains additional causally useful state`.

If an exact explicit O2 artifact cannot be isolated without extra developmental state, this arm must return `ARM_NOT_REALIZABLE` before E3 and cannot be silently approximated.

## Budget matching

For all realizable arms:

- same model/checkpoint;
- same temperature / deterministic policy;
- same maximum model calls per episode;
- same maximum generated tokens per episode;
- same maximum verifier calls per episode;
- same candidate-count ceiling;
- same source/test exposure;
- same timeout policy;
- same episode order;
- same admission predicates;
- same native verifier commands.

Sham padding may match state size but may not increase callable tools or semantic information.

Unused budget is recorded, not reallocated to another arm.

## Required run record

Every arm must record:

- branch/commit and protocol SHA-256;
- BugsInPy corpus identity and case identities;
- environment/runtime manifest;
- model/checkpoint/config/seed;
- exact allowed evidence presented at each episode;
- state hash before and after each episode;
- admitted operator/law IDs and hashes;
- proposal count and verifier count;
- model calls, tokens, wall time;
- residual sequence;
- old-closure result before any new construction;
- candidate hashes and verifier outcomes;
- terminal native verifier result;
- infrastructure status.

For FULL and ANCESTOR_MINUS, state evolution must be generated by the arm itself. Post-hoc copying of O1/O2 from another arm is forbidden.

## Reachable-frontier measurement

At the end of each episode, preserve the set or reproducible commitment to all candidates reached under the frozen discovery procedure and budget.

At minimum record these booleans when the named artifact is well-defined:

- `O2_reachable_from_A0`
- `O2_reachable_after_O1`
- `O3_reachable_from_A0`
- `O3_reachable_after_O1`
- `O3_reachable_after_O1_O2`

`reachable` means generated/evaluable under the frozen procedure and budget, not logically imaginable in hindsight.

If complete candidate-set capture is impractical, record a deterministic hash-chain plus counts and enough replay metadata to reproduce membership queries.

## E3 / O3 acquisition gate

An E3 repair alone is insufficient for an O3 claim.

A candidate O3 is counted as acquired only if all applicable gates pass:

1. E3 baseline residual is reproduced;
2. old admitted closure cannot already satisfy the E3 verifier;
3. candidate arises inside the frozen discovery budget;
4. candidate passes the E3 native/external verifier;
5. candidate is represented as a reusable operator/capability rather than only an opaque episode patch;
6. O3 ablation restores or materially weakens the E3 result under the frozen criterion;
7. the O3 artifact passes the prespecified protected-transfer check, if such a transfer target is already frozen before V145 execution.

If protected O3 transfer has not been frozen before execution, V145 may establish natural three-generation acquisition but not general O3 transfer.

## Primary causal hierarchy

The analysis must classify outcomes rather than emit a single permissive PASS.

### `PASS_V145_THREE_GENERATION_CAUSAL`

Requires all of:

- apparatus valid for required arms;
- FULL naturally admits O1 after E1;
- FULL naturally admits O2 after E2;
- FULL acquires verified O3 at E3;
- COLD does not acquire O3;
- O1_ONLY does not acquire O3;
- SHAM does not acquire O3;
- ANCESTOR_MINUS fails to reproduce the FULL developmental chain: either O2 is not acquired, O3 is not acquired, or the precommitted primary discovery-cost/frontier criterion materially worsens;
- O3 causal ablation passes;
- no semantic rescue or post-hoc target selection occurred.

This supports a bounded natural three-generation causal developmental claim.

### `PASS_V145_O2_SUFFICIENCY_AND_ANCESTRY`

If FULL and ORACLE_O2 acquire O3, while ANCESTOR_MINUS fails to acquire O2 or O3 and COLD/O1_ONLY/SHAM do not acquire O3, then the supported interpretation is:

- O1 is causally required to acquire the developmental bridge O2 under the frozen procedure;
- the explicit O2 artifact is sufficient for E3/O3 under the frozen procedure.

This is still a strong developmental result, but it does not establish hidden trajectory state beyond O2.

### `PASS_V145_TRAJECTORY_STATE_EXCEEDS_O2`

If FULL acquires O3 but ORACLE_O2 does not, while the other causal gates pass, record this separately.

Interpretation: the explicit O2 artifact is not a sufficient statistic for the causally useful developmental state carried by the FULL trajectory. This is evidence of a missing state representation, not permission to redefine O2 post hoc.

### `PARTIAL_V145_TWO_GENERATION_ONLY`

If O1 affects E2/O2 but no causal O3 staircase is established, retain the narrower result only.

### `NO_V145_DEVELOPMENTAL_EFFECT`

If matched developmental inheritance does not causally alter later verified acquisition under valid apparatus, record the negative.

### `INFRASTRUCTURE_NULL_V145`

Any mandatory arm that cannot execute its frozen runtime/verifier/case boundary invalidates the intended semantic comparison. Infrastructure nulls are retained and do not count as developmental failures.

## Strong frontier signature

The strongest preregistered frontier pattern is:

`O2 not reachable from A0`

`O2 reachable after O1`

`O3 not reachable from A0`

`O3 not reachable after O1 alone`

`O3 reachable after O1 + O2`

with ANCESTOR_MINUS moving the frontier backward.

This signature is sufficient to say that verified acquisition changed the set of later discoveries reachable under the same frozen search budget. It is not a claim of unbounded or open-ended self-improvement.

## Forbidden interpretations

A V145 result may not by itself establish:

- AGI or human-level intelligence;
- open-ended recursive self-improvement;
- model-weight learning unless weights are explicitly the manipulated state;
- universal transfer beyond the tested domains;
- that every later success depends on the entire trajectory;
- that raw memory, retrieval, or prompt length are ruled out unless the matched controls actually rule them out.

## No-rescue rule

After the first V145 arm executes, do not:

- change E1/E2/E3;
- change arm semantics;
- change the primary causal hierarchy;
- hand O1/O2/O3 to a failed natural arm;
- widen budgets for a failed arm;
- choose a friendlier O3 after seeing E3 outcomes;
- remove failed mandatory arms from the denominator;
- modify sham content using observed semantic failures.

A repaired apparatus receives a new run ID and preserves the null predecessor.
