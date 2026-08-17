# V153 ABC Control Mechanism Separator — Result

Date: 2026-08-18 NZST
Branch: `v153-abc-control-mechanism-separator`
Frozen checkpoint: `river://a25972d0-6711-4c05-8767-be061fc0e6ba/weights/ABC_training`
Base model: `Qwen/Qwen3.5-9B`
GitHub Actions run: `32055541816`
Artifact: `v153-abc-control-mechanism-separator`, artifact id `9296327464`, digest `sha256:c7b0f93d4f1d1b84af87fe9243d274c5bb3896e674f8d92d1ceb8f01f9d7de0a`

## Frozen held-out set

`violet, hidden, green, amber, silver, orange, teal, indigo`

Targets:

- A: `ka-{x}`
- AB: `ka-{x}-zu`
- ABC: `[ka-{x}-zu]`

No weight update occurred.

## Results

| Arm | A | AB | ABC |
|---|---:|---:|---:|
| A_NL_BASELINE | 0/8 | 0/8 | 8/8 |
| B_EXACT_TASK_INTERFACE | 0/8 | 0/8 | 8/8 |
| C_NL_PREFIX_HORIZON | 0/8 | 8/8 | 8/8 |
| D_EXACT_TASK_PREFIX_HORIZON | 0/8 | 8/8 | 8/8 |
| E_EXACT_TASK_PROMPT_ENSEMBLE any-hit | 0/8 | 0/8 | 8/8 |
| F_EXACT_TASK_PLUS_STAGE_CONTRACT | 0/8 | 0/8 | 8/8 |

Frozen-script classification: `MIXED_CONTROL_RESCUE`.

## Mechanism conclusions licensed by V153

1. **Not a simple prompt-interface mismatch.** The exact `Task: A / AB / ABC` interface used by the earlier three-skill training code still yields ABC for direct A and AB requests.
2. **Not rescued by ordinary prompt diversity.** The frozen exact-task prompt ensemble reaches A on 0/8 and AB on 0/8; ABC remains 8/8.
3. **Not rescued by an explicit terminal-stage contract.** Direct A and AB remain 0/8.
4. **AB remains reachable from an A-compatible intermediate state.** Seeding `ka-{x}` and allowing continuation restores exact AB on 8/8 under both natural-language and exact-task prompting.
5. **ABC remains reachable from an AB-compatible intermediate state.** The ABC prefix-horizon arm is 8/8.
6. **A-only terminal behavior remains unrecovered.** Even the A prefix-horizon arm is 0/8. The model continues beyond the A boundary rather than stopping at A.

## Claim boundary

V153 supports a selective-control / terminal-boundary residual on this frozen checkpoint. It does **not** by itself determine whether A's operator representation was erased, whether only its stopping/applicability boundary was overwritten, or whether a different lawful access horizon could still recover A. It does show that AB constituent structure is reachable despite direct AB selection failure.

## Next deciding separator

The highest-information next test is checkpoint-localization across the sequential training trajectory: evaluate the exact same A/AB/ABC probes on the frozen pre-A / A / AB / ABC checkpoints, and if available the immediate pre-save ABC checkpoint, to identify exactly where A terminal control and AB direct selection disappear. Pair that with token-level continuation diagnostics around the A stopping boundary.
