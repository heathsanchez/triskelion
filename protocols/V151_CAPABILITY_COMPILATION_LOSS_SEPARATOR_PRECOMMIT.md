# V151 — Capability-compilation loss separator

## Status

**PRECOMMITTED BEFORE V151 MODEL OUTCOMES**

V151 is a bounded diagnostic/causal separator on the clean second natural BugsInPy rung `youtube-dl/32`. It follows V149 and V150.

V149 repaired the source-context adapter and exposed the exact failing definition for T2, but all COLD and O1 unified-diff candidates failed transport before native verification. V150 replayed the exact frozen V149 outputs with a strict-then-`git apply --recount` transport normalization. That confirmed a real transport residual: two of six frozen O1 candidates became applicable and reached the native verifier, but neither solved; COLD remained 0/6 transportable and the three previously strict-applyable SHAM candidates remained semantic failures.

V150 therefore does not establish an O1 semantic advantage. It moves the residual from context/transport to the content represented by retained developmental state.

## Question

Did compiling the verified T1 acquisition episode into the frozen portable O1 object discard information that is causally useful for discovering a verified repair on T2?

This is a representation/memory separator, not a three-rung experiment.

## Frozen tasks and evidence

- T1 acquisition episode: `httpie/5`.
- T2 protected developmental target: `youtube-dl/32`.
- Model: `Qwen/Qwen3.5-9B`.
- Seeds: `[202608161, 202608162, 202608163]`.
- Maximum two repair calls per seed/arm.
- Maximum output: 2048 tokens per call.
- T2 context adapter: exact V149 failing-test -> definition resolver.
- Native verifier/runtime: exact historical BugsInPy adapter used by V149.

The T2 developer patch/fixed repair remains forbidden. V151 may inspect only the buggy T2 source selected by V149's deterministic context resolver plus native failing-test/verifier output from its own candidate.

## Frozen T1 identities

The verified T1 developer intervention must reproduce before any T2 model call and must have:

- intervention SHA-256: `b7f419e7993e92164969b7a99689f01dfa279ce2d1615e25fce0bb21486f472d`.

The compiled arm uses **exactly** the V149 frozen O1 capability, with artifact SHA-256:

`7ebb7fb26da6d137c13c1a08bafd7e540dbd52f25e04cf4298502e5ce5428546`

No O1 resynthesis, broadening, rewriting or applicability retuning is allowed.

## Output transport intervention

V151 does not use unified diff output. All arms use the already-existing structured-edit protocol:

```json
{"edits":[{"path":"relative/path.py","old":"exact unique existing source text","new":"replacement source text"}]}
```

Rules:

- 1–3 edits;
- `old` must occur exactly once in the buggy checkout;
- only existing Python production source may be edited;
- tests, tooling, generated environments and repository escapes are forbidden;
- edit application is deterministic exact text replacement;
- malformed/non-unique edits return transport feedback, not semantic verifier feedback;
- a native verifier call occurs only after a structured edit applies.

This format is arm-symmetric and was frozen before V151 outcomes. Its purpose is to remove unified-diff hunk accounting as a confound, not to add repair intelligence.

## Matched arms

Run every seed under all five arms:

1. `D_COLD`: T2 buggy evidence only.
2. `D_PLUS_O1_COMPILED`: exact frozen V149 O1 object appended.
3. `D_PLUS_RAW_T1`: the exact verified T1 acquisition evidence object that O1 synthesis consumed: failure class, failing-test tail, changed production file(s), and exact verified intervention diff. It is clearly labelled prior source-distinct verified acquisition evidence, not a proposed T2 patch.
4. `D_PLUS_SHAM_O1`: semantically empty control state matched exactly to serialized O1 memory character length.
5. `D_PLUS_SHAM_RAW`: semantically empty control state matched exactly to serialized RAW_T1 memory character length.

All arms otherwise receive exactly the same T2 visible evidence, seed, model, call budget, token budget, structured-edit instructions, verifier and stopping rule.

RAW_T1 intentionally contains more information than O1; V151 therefore does **not** interpret RAW-vs-O1 performance as a fair efficiency competition. RAW exists only to test whether useful causal information was lost during capability compilation. Its own equal-length sham controls context-volume effects.

## Primary classifications

Let an arm have a `REACHABILITY` advantage only if it solves strictly more of the three frozen seeds than `D_COLD` and its own length-matched sham. If solve counts tie, a prespecified `EFFICIENCY` advantage may be called only when the arm is no worse on solve count and has strictly lower median calls-to-native-verification success; if call medians tie, provider output tokens (or labelled output-character proxy if unavailable) may break the tie.

Classify:

### `PASS_V151_COMPILED_O1_CAUSAL_SIGNAL`

`D_PLUS_O1_COMPILED` has REACHABILITY or EFFICIENCY advantage over `D_COLD` and `D_PLUS_SHAM_O1`.

This revives the O1->O2 line under the corrected context/transport apparatus, but does not itself admit O2 unless a verified T2 repair exists and a separately governed O2 construction follows.

### `PASS_V151_CAPABILITY_COMPILATION_LOSS`

All of:

- RAW_T1 has REACHABILITY or EFFICIENCY advantage over `D_COLD` and `D_PLUS_SHAM_RAW`;
- compiled O1 has no advantage over `D_COLD` and `D_PLUS_SHAM_O1`;
- at least one RAW_T1 T2 candidate passes the native verifier.

Interpretation: the verified T1 episode contains developmentally useful information, but the current compiled capability object fails to preserve the causal carrier. This is a representation/memory residual, not a failure of developmental influence.

### `PASS_V151_BOTH_REPRESENTATIONS_SIGNAL`

Both RAW_T1 and compiled O1 have their respective causal advantages. O1 is not shown lossy on this endpoint.

### `NEGATIVE_V151_NO_T1_DEVELOPMENTAL_SIGNAL_WITHIN_BUDGET`

Neither RAW_T1 nor compiled O1 has a causal advantage after all apparatus gates pass.

This is the first result in this lineage that licenses treating `httpie/5 -> youtube-dl/32` itself as a bounded negative bridge under this model/budget, rather than blaming source-context or unified-diff transport.

### `R10_INCONCLUSIVE`

Any frozen T1 identity mismatch, historical-runtime failure, T2 reproduction failure, provider failure that destroys a matched comparison, or structured-edit apparatus defect invalidates the affected comparison.

## Secondary diagnostic

Record whether RAW_T1 and O1 alter:

- target production file;
- edit location/old-text identity;
- verifier-reached rate;
- first verifier residual class;
- second-attempt proposal after verifier feedback.

These are residual diagnostics only and may not replace the primary classification post hoc.

## Claim boundary

V151 cannot establish three-rung development, O3, open-ended self-improvement, or a general theorem that raw memory is superior to compiled capabilities. It tests one narrower question: whether the current O1 compilation retained the T1 information needed to causally alter T2 verified discovery under this frozen source-distinct BugsInPy/Qwen substrate.
