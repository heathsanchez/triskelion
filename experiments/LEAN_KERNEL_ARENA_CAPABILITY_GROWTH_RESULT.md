# Lean Kernel Arena capability-growth result

Date: 2026-08-14

## Claim boundary

This experiment establishes a real causal capability-growth result in an independently authored Lean proof checker under an independently authored external benchmark. It does **not** yet establish blind autonomous discovery of the repair: the representation change was designed after inspecting the exposed failure and nanoda source.

## Frozen external objects

- Checker: `ammkrn/nanoda_lib`
- nanoda revision: `418320295890faed83a96fd97907b12a3b6728c2`
- Lean Kernel Arena downloadable-suite run: `31005978773`
- Arena `test-tarball` artifact: `8931227426`
- Arena revision associated with that artifact: `8254ae7dc7d6c10dbea94b6761dcb1e4ccdfdee6`

The nanoda revision above is also upstream `master` at the time of the experiment.

## Exposed obstruction

Arena case `level-index-out-of-order` is valid but original nanoda declines it.

The parser treated the export format's external internalization-table identifiers (`in`, `il`, `ie`) as if they were the checker DAG's dense insertion positions. The missing distinction was:

```text
external identifier != internal storage location
```

The repair introduced explicit maps:

```text
external Name ID  -> internal NamePtr
external Level ID -> internal LevelPtr
external Expr ID  -> internal ExprPtr
```

The patch replaced 2 Name, 4 Level, and 10 Expr binding sites with the mapped representation.

## Causal two-case result

Exact Arena static cases:

| Condition | level-index-out-of-order | sparse-name-index | dense controls |
|---|---:|---:|---:|
| original nanoda | decline (2) | decline (2) | accept, accept |
| repaired nanoda | accept (0) | accept (0) | accept, accept |
| repair ablated | — | decline (2) | — |

Precommitted gates all passed:

- old-closure obstruction
- necessity on exposed case
- held-out transfer
- causal ablation
- dense controls preserved

Workflow: `.github/workflows/lean-kernel-arena-growth.yml`
Initial successful run: `31786914317`

## Static Arena sweep

Across every static NDJSON test in the frozen Arena repository snapshot used by the sweep:

- baseline: 6/8 correct
- repaired: 8/8 correct
- gains: `level-index-out-of-order`, `sparse-name-index`
- regressions: 0

Workflow: `.github/workflows/lean-kernel-arena-static-sweep.yml`
Successful run: `31787796356`

## Metamorphic generalization

Generated 256 semantically equivalent encodings of the same valid Lean object with randomized external Name, Level, and Expr identifiers, including gaps and out-of-order IDs.

- original nanoda: 0/256 accepted
- repaired nanoda: 256/256 accepted
- malformed negative controls: 512/512 rejected
- causal ablation subset: 32/32 valid variants failed again after removing the repair

The negative controls included dangling level references and duplicate external expression bindings.

Workflow: `.github/workflows/lean-kernel-arena-id-metamorphic.yml`
Successful run: `31787981729`

## Closure-before-invention

Seven later tutorial cases initially appeared to expose a different capability around duplicate/misnamed inductive declarations. Inspection showed original nanoda was declining upstream on the same continuous-back-reference assumption before reaching its existing invalid-declaration checks.

Therefore no new primitive was added. The retained representation capability was applied unchanged.

Arena-normalized outcome (`0=accept`, `2=decline`, anything else=`reject`):

- before repair: all seven later cases declined
- after repair: all seven later cases correctly rejected
- existing duplicate-definition rejection remained a rejection
- new primitive count: 0
- closure gains: 7

Workflow: `.github/workflows/lean-kernel-arena-tutorial-closure.yml`
Corrected successful run: `31788774406`

## Full downloadable Arena suite

The immutable Arena test artifact contains 161 tests under the download-size limit:

- 103 good / expected accept
- 58 bad / expected reject

Results:

| Metric | Original nanoda | Repaired nanoda |
|---|---:|---:|
| total correct | 152/161 | **161/161** |
| valid accepted | 101/103 | **103/103** |
| invalid rejected | 51/58 | **58/58** |
| declines | 9 | **0** |
| false accepts | 0 | **0** |
| regressions | — | **0** |

Exactly nine statuses changed:

- valid -> accepted: `level-index-out-of-order`, `sparse-name-index`
- invalid decline -> reject: tutorial cases 130, 131, 132, 133, 134, 135, 136

No other test changed status.

Workflow: `.github/workflows/lean-kernel-arena-full-small-suite.yml`
Successful run: `31788774456`

## Interpretation

The strongest supported causal chain is:

```text
independent verified failure
-> missing representational distinction
-> explicit reusable capability
-> original target becomes reachable
-> independent target becomes reachable
-> broad metamorphic generalization
-> malformed controls remain rejected
-> later superficially different failures are solved by closure, not invention
-> removing the capability destroys the acquired behavior
```

The important closure result is that one capability explains all nine original declines in the downloadable Arena suite: two valid cases become accepted and seven invalid cases progress far enough to be correctly rejected. The system therefore gains both completeness and effective negative discrimination from the same representation repair.

## What remains unproved

The decisive missing gate is **blind autonomous discovery**. A future experiment must precommit a fresh checker/target stream before the discovering agent sees the protected cases, allow the agent to inspect only the exposed failure and checker source, and then evaluate generated changes on protected independent cases. The current experiment proves the mechanism, transfer, causal necessity, generality, and closure behavior, but not that an agent autonomously discovered the abstraction under a blind protocol.
