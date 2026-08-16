# V145R1 — Contamination-Aware Third Natural Rung Eligibility

## Status

**PRECOMMITTED BEFORE V145R1 EXECUTION**

V145R1 is a successor eligibility experiment, not a rewrite of V141 or V145. V141's original result remains retained. V145's original `pandas/66` preregistration remains retained but is blocked for the strongest blind-natural developmental claim because a preexecution audit found prior semantic exposure to that repair.

## Question

Does the frozen V141 natural-episode stream contain a third real episode that is both:

1. apparatus/semantically eligible under the exact V141 rule; and
2. not present in the frozen known-semantic-exposure denylist?

## Frozen inheritance from V141

The following are unchanged:

- corpus: frozen BugsInPy 501-bug / 17-project lineage;
- project for this continuation: `pandas`;
- candidate rank: lowercase hexadecimal `SHA256("pandas/<bug_id>")`;
- order: lexical hexadecimal ascending;
- semantic qualification: fixed version passes native test AND buggy version fails native test;
- runtime apparatus: `cp3/bugsinpy_exact_runtime.py`;
- no semantic skipping;
- infrastructure failures do not update the semantic hypothesis.

The authoritative corpus lock remains:

`760b73f87bbe79b76c970c1b2ac4cdd83e5eb18ee3f4b9f2304a915fddbbd5ad`

## Added exposure gate

Before runtime qualification, a candidate whose exact `project/id` appears in `protocols/V145R1_EXPOSURE_DENYLIST.json` is recorded as:

`EXPOSURE_INELIGIBLE`

and is not executed as a semantic qualification candidate.

This is not a semantic failure. It records that the case cannot support the strongest blind-natural discovery claim because its repair/source semantics were previously inspected by the research lineage.

The denylist is frozen before this run. It may not be changed using V145R1 runtime outcomes.

## Selection

Walk all pandas bug IDs in the exact V141 SHA order.

For each candidate:

1. if frozen-denylisted, append an `EXPOSURE_INELIGIBLE` record and continue;
2. otherwise run the exact V141 buggy/fixed qualification apparatus;
3. retain infrastructure failures as infrastructure records and continue according to the inherited qualification semantics;
4. retain semantic nonqualifications;
5. stop at the first non-denylisted case with `fixed_pass_buggy_fail`.

No fixed production source, developer patch, issue/PR solution narrative, or repair semantics may be read to decide selection.

## Post-selection exposure audit

The selected case is only **provisionally clean against the frozen known-exposure denylist**. Before it is installed as E3 in a causal successor to V145, perform the separately frozen retrospective exposure-search procedure over prior project artifacts.

If that audit discovers prior semantic exposure:

- do not reinterpret the qualification result;
- append the exposure evidence;
- mark the case `RETROSPECTIVE_EXPOSURE_INELIGIBLE` for the crown-jewel claim;
- rerun the same deterministic stream with a new run ID and the newly frozen evidence manifest.

This makes contamination removal monotone and auditable rather than a semantic cherry-picking mechanism.

## Verdicts

- `PASS_V145R1_PROVISIONAL_CLEAN_E3_EXISTS`: first exact-runtime V141-qualified candidate exists and is absent from the pre-frozen known-exposure denylist.
- `EXHAUSTED_V145R1`: no such pandas candidate remains.
- `R10_INCONCLUSIVE`: corpus or apparatus validity prevents interpretation.

A V145R1 pass does **not** yet establish O3, developmental dependence, or full retrospective cleanliness. It licenses the post-selection exposure audit only.
