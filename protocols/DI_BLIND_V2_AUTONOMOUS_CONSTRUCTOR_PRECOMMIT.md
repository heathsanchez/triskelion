# DI Blind V2 — autonomous construction precommit

Status: FROZEN BEFORE V2 TARGET EXPOSURE

## Why V2 exists

V1 returned `VALID_NEGATIVE_NO_CONSTRUCTION`. Seven of eight generations were rejected at the experiment interface and the sole admissible exact-string edit built but did not repair the exposed case. V2 changes **only the generic patch representation and preregistered proposal budget**. It does not add any diagnosis, target-specific operator, known repair, AST template, or semantic hint from V1.

V1 remains a negative result and is not rerun or rescued.

## Scientific question

Can a frozen model, given one mechanically selected natural failure of an independent Lean checker plus the allowed frozen source, autonomously construct a source change which:

1. fixes that exposed failure;
2. passes a hidden regression gate;
3. is retained before protected transfer cases are evaluated;
4. improves at least one later protected case the frozen checker gets wrong; and
5. is causally necessary under physical remove/rebuild/restore/rebuild ablation?

A V2 pass establishes only bounded blind autonomous capability construction with protected causal reuse. It does **not** establish developmental compounding. The O1→O2 experiment is a separate subsequent gate.

## Frozen external substrate

- checker repo: `pmatos/vow-lean-kernel`
- checker revision: `514ab33fc0262c491a0af1846cc3887f48411e36`
- Vow revision: `15c1b933f87eed2b23c176665730baea37706daa`
- Lean Kernel Arena revision: `8254ae7dc7d6c10dbea94b6761dcb1e4ccdfdee6`
- Arena workflow run: `31005978773`
- Arena artifact id: `8931227426`
- V2 ordering salt: `TRISKELION_BLIND_VOW_V2_LINEPATCH`
- V1 exposed SHA, excluded solely because it is no longer blind: `323a6140d9acc906193ddc22fa4f3391a3f259357853427c2f82382c71a1e051`

The V2 target is the first baseline-incorrect case in the V2 salted order whose SHA is not the prior V1 exposed SHA. No semantic selection or manual case inspection is permitted.

## Frozen proposer

- model: `Qwen/Qwen3.5-9B`
- provider path: River
- base-weight updates: `0`
- generations: `16`
- seed: `20260819`
- temperature: `0.7`
- max generation tokens: `2200`
- proposer sees exactly:
  - one exposed failing NDJSON case;
  - its baseline checker result/output tail;
  - lexically selected `kernel/**/*.vow` source up to the frozen source budget;
  - numbered source lines and the generic edit schema.
- proposer does **not** see:
  - protected corpus cases or filenames;
  - V1 candidate outputs;
  - manual diagnostic traces;
  - the known nanoda intervention;
  - a hand-written hypothesis about the failure;
  - target-specific repair primitives.

## V2 generic patch representation

V1's exact-substring quoting requirement discarded most model proposals for formatting reasons. V2 permits exactly one deterministic line-range replacement:

```json
{
  "hypothesis": "free text",
  "path": "kernel/.../*.vow",
  "start_line": 1,
  "end_line": 1,
  "new_text": "replacement text"
}
```

Rules frozen before target exposure:

- `path` must be one of the source files shown to the proposer;
- `start_line` and `end_line` are 1-based, inclusive, within that file;
- at most 40 existing lines may be replaced;
- replacement may contain at most 80 lines and 12,000 UTF-8 characters;
- replacement must differ from the original selected range;
- exactly one file/range edit is allowed;
- no tests, harnesses, build files, inputs, generated binaries, or external dependencies may be changed.

This representation is intentionally generic. It gives the model no information about what repair should be made; it only prevents a correct idea from being rejected because the model failed to reproduce a long source substring byte-for-byte.

## Hard blinding order

1. clone/build frozen checker;
2. download Arena corpus;
3. compute complete salted manifest and commitment;
4. mechanically select exactly one fresh unresolved case;
5. persist only that exposed case, its baseline output, and cryptographic commitments;
6. delete the complete Arena corpus and temporary archive;
7. call the proposer and generate all 16 candidates;
8. validate candidates only against the exposed source/edit schema;
9. hash and seal the entire candidate batch;
10. only then re-download the Arena corpus;
11. reproduce the original corpus commitment;
12. evaluate candidates in generation order;
13. retain the first candidate satisfying exposed repair + hidden regression gate;
14. freeze that choice permanently;
15. only then evaluate protected transfer and causal ablation.

## Hidden regression gate

The retained candidate must pass the first 32 post-exposure cases in V2 order that the frozen checker gets correct. These cases are unavailable to the proposer.

## Protected transfer

After retention, evaluate the remaining post-exposure suffix excluding regression cases. A protected transfer is a case where:

`frozen checker = incorrect` and `developed checker = correct`.

At least one such case is required for a full pass.

## Causal ablation

For every claimed protected transfer:

1. physically restore the pristine source range;
2. rebuild the checker;
3. require behavior to return to the frozen baseline;
4. reapply the exact retained model-generated line patch;
5. rebuild again;
6. require correct behavior to return.

## Frozen verdicts

- `PASS_DI_BLIND_V2_AUTONOMOUS_CONSTRUCTION`: retained autonomous edit + >=1 protected transfer + complete remove/restore causal ablation.
- `PARTIAL_V2_EXPOSED_ONLY`: a candidate repairs exposed + hidden regressions but yields no causally verified protected transfer.
- `VALID_NEGATIVE_V2_NO_CONSTRUCTION`: no candidate clears exposed + hidden regression gates.
- infrastructure failure: null, not a capability negative.

No post-result hinting, candidate regeneration, target-specific prompt editing, manual repair insertion, or rerun on the same V2 exposed case is permitted.

## Result publication

Unlike V1, the completed `result.json`, precommit, exposed metadata, candidate hashes, and candidate evaluation summary must be committed to `results/di_blind_v2/` by CI after the scientific verdict. A green workflow is never itself the verdict.

## Next gate if V2 passes

Freeze the retained V2 edit as autonomous `O1`. Before exposing the next target, preregister matched cold and `D0+O1` discovery arms with identical model/candidate/budget rules. The developmental crown-jewel requires:

`O2 ∉ Reach(D0, B)` but `O2 ∈ Reach(D0 + O1, B)`

with O2 itself autonomously generated, independently verified, and causally ablated.
