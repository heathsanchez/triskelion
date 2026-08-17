# V160 Quix Experiential Rescue — frozen protocol

## Question
Can an explicit map learned only from prior verified coding experience preserve or restore earlier executable repair capability after later neural interference, outperforming both frozen weights alone and raw verified memory?

## Frozen lineage
- Base model: Qwen/Qwen3.5-9B
- Seed: 20260831
- Starting checkpoint: `river://ae6fa294-181b-46af-b078-429ce7e6c882/weights/quix_AB_step1`
- Source benchmark lineage: QuixBugs commit `4257f44b0ff1181dedaedee6a447e133219fcebf`
- Tasks: A shunting-yard missing stack append; B factorization missing prime return; C bitcount missing bit-clearing update.

## Split
- Neural interference train worlds: 0..15.
- Prior verified experience worlds: 80,81.
- Protected evaluation worlds: 100..107.

## Procedure
1. Load the already successful AB checkpoint.
2. On worlds 80,81, obtain model repair lines for A and B and admit them only if the executable verifier passes.
3. Learn one explicit template per task by generic string anti-unification: replace the common numeric world id with a slot. Freeze these maps before protected evaluation.
4. Starting again from the same AB checkpoint, train only C at the original LR `2e-4` and original batch size 16, with no A/B replay. After every update, executable-test A/B/C on protected worlds.
5. Stop at the first update where A or B falls below 6/8, or after 12 updates. If no regression occurs, verdict is `NO_INTERFERENCE_WITHIN_BUDGET`.
6. Freeze the first-regression weights and evaluate four arms on protected worlds:
   - neural only;
   - raw verified memory (same two admitted prior repair lines placed in the prompt);
   - compiled experiential map (instantiate the frozen learned template; no protected answer lookup);
   - shuffled map (swap A/B maps; same structural budget).
7. C remains neural-only in compiled/shuffled arms so rescue of A/B cannot trade away C by changing weights.

## Decisive success
`PASS_REAL_CODING_EXPERIENTIAL_RESCUE` iff compiled-map A+B verified hits exceed both neural-only and raw-memory A+B hits and exceed shuffled-map A+B hits.

## Claim boundary
A pass establishes bounded causal preservation/rescue of executable coding capability by explicit structure learned from prior verified experience under a frozen variable-renaming protocol. It does not establish unrestricted program repair, natural-world operator discovery, or open-ended self-improvement.
