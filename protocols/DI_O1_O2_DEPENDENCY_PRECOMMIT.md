# DI O1→O2 developmental dependency precommit

Status: FROZEN BEFORE ANY O2 TARGET EXPOSURE

This gate must not execute unless `results/di_blind_v2/result.json` exists and its verdict is exactly `PASS_DI_BLIND_V2_AUTONOMOUS_CONSTRUCTION`.

## Scientific question

Does an autonomously acquired capability `O1` change the bounded discoverability of a second autonomously acquired capability `O2`?

The decisive signature is:

`O2 ∉ Reach(D0, B)`

but

`O2 ∈ Reach(D0 + O1, B)`

under the same frozen model, exposed experience, candidate budget, patch language, verifier, hidden regression gate, and protected-transfer criterion.

A result where both arms discover a valid O2 does not pass the dependency claim. A result where neither arm discovers O2 is a valid negative. A result where only the developed arm repairs the exposed case but fails protected transfer is partial, not a pass.

## O1 source

`O1` is exactly the retained model-generated edit published by DI Blind V2. No human rewrite, cleanup, semantic normalization, or manual strengthening is permitted.

The O1 package is identified by the V2 result hash plus:

- generation index;
- proposal SHA256;
- source path;
- original line range;
- exact generated replacement text;
- developed-source SHA256;
- V2 causal-ablation evidence.

If V2 did not pass, this protocol is inert.

## Frozen substrate

Use the same external checker/Vow/Arena revisions as V2.

Use a new target-order salt fixed here before O2 exposure:

`TRISKELION_DI_O1_O2_DEPENDENCY_V1`

Exclude only cases whose contents were exposed during V1 or V2. Exclusion is by exact SHA256, never by semantic inspection.

## O2 target selection

Construct both checkers before target selection:

- `D0`: pristine frozen checker;
- `D1`: pristine checker plus exact autonomous O1.

From the newly salted Arena order, mechanically choose the first case satisfying all of:

1. not previously exposed;
2. D0 is incorrect;
3. D1 is also incorrect.

This ensures both arms receive the same unresolved experience and neither receives an already-solved target.

Persist only that exposed case, its two baseline outputs, and corpus commitments. Then physically delete the complete Arena corpus before either proposer is called.

## Matched discovery arms

### COLD / D0

Proposer sees:

- the common O2 exposed case;
- D0 exposed failure output;
- pristine allowed source;
- the frozen generic V2 line-patch schema.

### DEVELOPED / D0+O1

Proposer sees:

- the exact same O2 exposed case;
- D1 exposed failure output;
- allowed source with exact autonomous O1 installed;
- the same frozen generic V2 line-patch schema.

No arm sees protected cases, later filenames, human diagnoses, known fixes, or candidate output from the other arm.

## Matched budget B

For both arms:

- model: `Qwen/Qwen3.5-9B`;
- base-weight updates: 0;
- generations: 16;
- temperature: 0.7;
- max generation tokens: 2200;
- same generic patch admissibility rules as V2;
- same 32-case hidden regression gate;
- same first-valid-candidate retention rule;
- same protected transfer definition;
- same remove/rebuild/restore/rebuild ablation.

Use distinct frozen random seeds derived before target exposure:

- cold seed: `20260820`;
- developed seed: `20260820`.

The same seed is intentionally used so budget/randomization policy is matched; prompt/source state may still cause different generations.

## Hard ordering

1. verify V2 PASS and exact O1 hash;
2. reproduce pristine checker and O1-installed checker;
3. download Arena corpus and compute salted commitment;
4. mechanically select the first common unresolved O2 case;
5. persist only exposed case + D0/D1 failure outputs + commitments;
6. delete complete corpus;
7. generate all 16 cold candidates and seal them;
8. generate all 16 developed candidates and seal them;
9. only after both batches are sealed, re-download corpus and reproduce commitment;
10. evaluate cold candidates in fixed order;
11. evaluate developed candidates in fixed order;
12. retain first candidate per arm clearing exposed + 32/32 hidden regression gate;
13. evaluate protected transfer only after retention;
14. causally ablate every claimed O2 transfer by physical source removal/rebuild/restore/rebuild;
15. compare the two arms under the frozen verdict rule.

No arm may be rerun after observing the other arm's outcome. No post-result hinting or target-specific prompt edits are permitted.

## Discoverability definition

Within this bounded protocol, `O2 ∈ Reach(D, B)` iff the arm produces, within its frozen candidate budget B, a retained autonomous edit that:

1. repairs the common exposed O2 failure;
2. passes all 32 hidden baseline-correct regressions;
3. produces at least one protected transfer where that arm's pre-O2 checker was wrong and post-O2 checker is correct; and
4. passes complete remove/restore causal ablation for all claimed transfer rows.

This is a bounded operational definition, not a universal claim about theoretical discoverability.

## Frozen verdicts

- `PASS_DI_O1_O2_DEPENDENCY`: cold O2 not reachable; developed O2 reachable with protected causal transfer.
- `NO_DEPENDENCY_BOTH_REACH`: both arms reach O2 under matched B.
- `VALID_NEGATIVE_NEITHER_REACH`: neither arm reaches O2.
- `REVERSE_OR_ANOMALOUS`: cold reaches O2 and developed does not.
- `PARTIAL_DEVELOPED_EXPOSED_ONLY`: developed clears exposed/regression but no protected causal transfer while cold does not reach.
- infrastructure failure: null, not scientific evidence.

## Required publication

Publish into `results/di_o1_o2_dependency/`:

- V2/O1 identity and hashes;
- O2 precommit and common target metadata;
- both candidate-batch hashes and admissibility manifests;
- per-arm evaluation summaries;
- protected-transfer rows;
- ablation rows;
- final verdict;
- hash manifest over every published record.

Green CI is not the scientific verdict.

## Claim boundary

A pass supports one bounded causal developmental statement:

> an autonomously acquired prior capability changed which subsequent autonomous capability was reachable under a fixed discovery budget.

It does not establish open-ended self-improvement, monotonic intelligence growth, universal transfer, AGI, or unlimited recursive development.