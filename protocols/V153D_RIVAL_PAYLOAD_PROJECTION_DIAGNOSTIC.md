# V153D — Zero-call rival payload projection diagnostic

Frozen: 2026-08-16 NZST
Controller: Rigorous Breakthrough Stack v1.1

## Status

POST-HOC DIAGNOSTIC ONLY. This protocol cannot retroactively convert V153 into a PASS and cannot earn a developmental causal claim.

## Frozen source evidence

The only model outputs used are the immutable V153 Actions artifact from run `31943774314`, artifact `v153-set-valued-rival-search`, whose GitHub artifact digest is:

`sha256:0368ed7c6d45e053491c90fd3969dad13222fa86cd3f67051737454ff10c8a5e`

No new model call is permitted.

## Residual

V153 required call 2 to return one JSON object containing exactly three ranked alternatives. In two RAW T1 seeds, the model emitted repair payloads whose outer envelope/diagnosis serialization was malformed, causing the strict V153 parser to reject the response. A byte audit after V153 showed literal `"edits":` fields whose array values were independently JSON-decodable.

## Question

Were distinct rival repair payloads already present in the immutable V153 RAW bytes, and if the controller had projected only the semantically operative `edits` field, would the deterministic first-distinct rival have reached and/or passed the native verifier?

## Projection adapter

For each RAW call-2 response, scan left-to-right for the exact literal JSON key token `"edits":`. At each occurrence, invoke the standard JSON decoder beginning immediately after the colon. Accept the value only if it decodes as an array and validates unchanged through `structured_edit_protocol_v2.extract_edits` when wrapped as `{ "edits": value }`.

The adapter:

- does not modify any decoded edit string;
- does not repair path/old/new values;
- ignores diagnosis text completely because diagnosis was never an argument to V153 controller selection;
- preserves byte order of successfully decoded `edits` fields;
- deduplicates only by canonical payload SHA-256, exactly as V153 did;
- selects the first canonical payload whose SHA-256 differs from the frozen call-1 payload SHA-256;
- never falls through to a later payload based on verifier outcome.

## Native replay

For each RAW seed with a selected projected rival:

1. prepare a fresh exact-runtime buggy checkout of `youtube-dl/32` using the unchanged precompiled apparatus;
2. apply the selected canonical structured edit;
3. run the exact native verifier once.

No model or synthesis call occurs.

## Diagnostic classifications

- `DIAGNOSTIC_V153_PAYLOAD_RIVALS_PRESENT` iff at least 2/3 RAW seeds contain at least one valid projected payload distinct from call 1.
- `DIAGNOSTIC_V153_PAYLOAD_RIVALS_REACH_VERIFIER` iff at least one such selected payload applies and reaches the native verifier.
- `DIAGNOSTIC_V153_PAYLOAD_RIVAL_SOLVES_T2` iff any selected payload passes the native verifier.

A solve is evidence about the frozen V153 candidate bytes, not a prospective V153 causal PASS.

## Next-step boundary

If payload rivals are present on >=2/3 seeds, a prospective successor may change only the call-2 representation adapter to field projection and rerun the frozen matched arms. If they are absent, no such adapter repair is licensed.
