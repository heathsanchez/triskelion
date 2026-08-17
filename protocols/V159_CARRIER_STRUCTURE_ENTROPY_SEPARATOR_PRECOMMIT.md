# V159 CARRIER STRUCTURE × ENTROPY SEPARATOR — PRECOMMIT

## Residual

V157 prospectively established that semantic wrapper labels and semantic JSON contents are not required for the call-2 rival-execution effect: MATCHED_LABELLED and a same-length OPAQUE_ENVELOPE both produced the effect while COLD did not. V157 therefore leaves a narrower unresolved question: which nonsemantic carrier property is causally responsible?

The two strongest remaining candidate explanations are:

1. **STRUCTURE** — JSON-like nesting/punctuation/field segmentation induces a different search policy;
2. **ENTROPY/DIVERSITY** — a long heterogeneous token/character stream induces the change even without JSON structure.

V159 freezes a 2×2 carrier experiment to separate those axes in one prospective run.

## Fixed apparatus

Inherit unchanged from V157:

- model/provider: `Qwen/Qwen3.5-9B` through the same River provider;
- T1: BugsInPy `httpie/5`;
- T2: BugsInPy `youtube-dl/32`;
- seeds: `[202608161, 202608162, 202608163]`;
- two-call, 2048-token budget;
- structured-edit protocol and deterministic first-valid-distinct rival selection;
- persistent post-call-1 workspace;
- V155 current-source synchronization;
- exact historical native verifier/runtime;
- V156 `RIVAL_EXECUTION_SUCCESS` endpoint;
- no protected information, target tuning, extra model calls, or extra verifier calls.

The V157 opaque carrier is the positive reference. V159 does not alter task semantics, source context, failure feedback, or call budget.

## Frozen carrier construction

Start from the exact V157 `OPAQUE_ENVELOPE` string `O`, with length `N`.

Define four non-cold carrier arms arranged as a 2×2 design:

### 1. STRUCTURED_HIGH — structure=1, entropy=1

Exact V157 `OPAQUE_ENVELOPE`.

### 2. FLAT_HIGH — structure=0, entropy=1

Starting from `O`, preserve every ASCII letter, digit and newline in exactly the same position. Replace each JSON/wrapper structural punctuation character in the frozen set

`{}[],:\"`

with a space. All other characters are unchanged.

This preserves length, letter identities/positions, digit positions, newline positions and overall high lexical diversity while destroying parseable JSON structure and quote/delimiter segmentation.

### 3. STRUCTURED_LOW — structure=1, entropy=0

Preserve every non-letter character of `O` exactly, including all braces, brackets, quotes, colons, commas, digits, whitespace and newlines. Replace every ASCII alphabetic character by `x` or `X` preserving case.

This preserves exact structural layout and length while collapsing alphabetic diversity.

### 4. FLAT_LOW — structure=0, entropy=0

Apply both transformations: collapse ASCII letters to `x`/`X`, and replace the frozen structural punctuation set `{}[],:\"` with spaces. Preserve digits, all other punctuation, whitespace and newline positions. Length remains exactly `N`.

### 5. COLD

No retained carrier.

## Construction invariants

Before any model sampling:

- all four non-cold carriers must have exactly the same character length `N`;
- STRUCTURED_HIGH must equal the exact V157 opaque carrier construction;
- STRUCTURED_HIGH and STRUCTURED_LOW must retain identical non-letter character positions;
- FLAT_HIGH and FLAT_LOW must have no characters from the frozen structural punctuation set;
- FLAT_HIGH must preserve every letter/digit/newline position and value from STRUCTURED_HIGH except frozen punctuation positions;
- STRUCTURED_LOW and FLAT_LOW must contain no ASCII alphabetic characters other than `x` or `X`;
- STRUCTURED_HIGH must parse as V157 opaque JSON after the first newline; STRUCTURED_LOW is not required to parse because key collisions after alphabet collapse may occur and parseability is not the manipulated variable;
- no arm may contain task-semantic strings intentionally introduced by V159.

Any invariant failure returns `R10_INCONCLUSIVE_V159_CONTROL_CONSTRUCTION` before provider creation.

## Primary endpoint

Per seed, `RIVAL_EXECUTION_SUCCESS` is exactly V156/V157:

1. synchronized call 2 occurs after native-verifier falsification of call 1;
2. exactly three alternatives are emitted;
3. all three are valid structured-edit payloads;
4. all three are distinct from call 1;
5. deterministic selected rival applies to the actual persistent post-call-1 workspace;
6. selected rival reaches the native verifier.

Task solve remains separately reported and cannot override the carrier-mechanism verdict.

Let success counts out of 3 be:

- `SH` = STRUCTURED_HIGH
- `FH` = FLAT_HIGH
- `SL` = STRUCTURED_LOW
- `FL` = FLAT_LOW
- `C` = COLD

## Frozen interpretation hierarchy

1. Construction invariant failure -> `R10_INCONCLUSIVE_V159_CONTROL_CONSTRUCTION`.
2. Any arm has fewer than 3 comparable seeds -> `R10_INCONCLUSIVE_V159`.
3. `SH < 2` -> `OBSTRUCTED_V159_V157_EFFECT_NOT_REPLICATED`.
4. If `FH >= 2`, `FL >= 2`, and `abs(SH-FH) <= 1` -> `NEGATIVE_V159_JSON_STRUCTURE_NOT_REQUIRED`.
5. Else if `SL >= 2`, `FL < 2`, and `FH >= 2` -> `PASS_V159_STRUCTURE_ENTROPY_INTERACTION`.
6. Else if `SL >= 2`, `FH < 2` -> `PASS_V159_STRUCTURE_DOMINANT`.
7. Else if `FH >= 2`, `SL < 2` -> `PASS_V159_ENTROPY_DOMINANT`.
8. Else if `SL < 2`, `FH < 2`, and `FL < 2`, while `SH >= 2` -> `PASS_V159_STRUCTURE_AND_ENTROPY_JOINTLY_REQUIRED`.
9. Else -> `OBSTRUCTED_V159_INTERMEDIATE_CARRIER_SEPARATION`.

For every verdict, report all five success counts and task-solve counts. Do not infer semantic learning from any carrier-only effect.

## Scientific purpose

A decisive V159 outcome changes the architecture:

- if structure dominates, retained-state serialization is a causal search-policy control surface;
- if entropy dominates, token-stream diversity/occupancy is the likely carrier-level control surface;
- if interaction is required, the effect depends on structured heterogeneous context;
- if FLAT_LOW also preserves the effect, the remaining explanation collapses toward coarse context length/presence rather than memory structure.

The purpose is to identify what actually moves search policy `D` before using retained-state effects as evidence for developmental knowledge.

This protocol is frozen before any V159 model outcome is sampled.
