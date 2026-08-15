# CP3 protected four-arm implementation precommit v1

Status: **FROZEN BEFORE PROTECTED SOURCE OPENING**

This file operationalizes the already-frozen `FOUR_ARM_PROTOCOL.json` and `PROTECTED_EVAL_GATE.md`. It does not change the scientific corpus, cases, model, budgets, or causal comparison.

## Protected cases and order

Exactly, in this order:

1. `thefuck/32`
2. `keras/32`
3. `spacy/2`
4. `fastapi/5`
5. `black/18`

No replacement, skipping, or post-hoc exclusion is permitted. Infrastructure failures remain infrastructure failures.

## Allowed protected input

For each case, construct the input only from the **buggy revision** and its native failing verifier execution. Never open the fixed revision, developer patch, prior solution trace, or protected outcome labels before the cell is scored.

The sanitizer is deterministic:

- include the native failing-test output, truncated to the final 12,000 characters;
- extract Python file paths mentioned by that output;
- keep only files inside the buggy checkout, excluding tests, virtual environments, `.git`, caches, and generated/vendor directories;
- include at most the first 3 distinct referenced production files in traceback order;
- if no production path is mentioned, include the first 3 lexicographically sorted production `.py` files;
- include at most 8,000 characters per source file, centered on referenced line numbers when available, otherwise from file start;
- strip absolute temporary-directory prefixes;
- do not include project metadata that exposes the fixed commit or patch.

The resulting sanitized text is hashed before any arm-specific memory is added. The same sanitized text is used in all four arms.

## Frozen arm semantics

- **COLD**: sanitized protected input only; no acquisition memory or capability text.
- **RAW_MEMORY**: prepend the two raw acquisition verified intervention traces (`httpie/5`, `youtube-dl/32`) exactly as acquisition evidence, without routing or compression. No protected evidence is present.
- **ALWAYS_ON**: prepend every `memory_text` from the frozen acquisition capability payload, in frozen capability order, regardless of applicability.
- **VERIFIED**: deterministic capability activation. Lowercase the sanitized protected input. A capability activates iff at least one frozen `scope.any_terms` string occurs as a literal substring. Only activated capabilities' `memory_text` values are prepended. Activation decisions and matched terms are recorded before the model call.

No arm may see another arm's output or verifier result.

## Frozen model and budget

- provider model: `Qwen/Qwen3.5-9B` (`Qwen3.5-9B` in result schema)
- temperature: `0`
- per-case seed: `20260815 + protected_case_index`; the same seed is used for all four arms of that case
- maximum model calls per case-arm: `2`
- maximum tokens per call: `2048`
- exactly one native protected verifier evaluation per case-arm

Call 2 is allowed **only** if call 1 cannot be parsed/applied mechanically. Call 2 receives the original prompt plus the invalid model text and a formatting/application error; it receives no native verifier feedback. If call 1 is mechanically applicable, call 2 is not used.

## Frozen model output contract

The model must return one JSON object:

```json
{
  "edits": [
    {"path": "relative/production.py", "search": "exact old text", "replace": "new text"}
  ],
  "rationale": "short explanation"
}
```

Constraints enforced mechanically:

- 1 to 4 edits;
- paths must be existing production files inside the buggy checkout;
- no test files may be edited;
- every `search` must be non-empty and occur **exactly once** in the named file at application time;
- edits are applied in listed order;
- no shell commands, dependency changes, new files, file deletion, or network actions are accepted;
- an unparseable/unapplicable proposal after the allowed formatting retry receives terminal `FAIL` without running the native verifier; this is recorded as verifier `ran=false` and is counted as a failed cell, not silently excluded.

## Scoring

If a candidate applies, run the BugsInPy native relevant-test verifier exactly once. `PASS` means the relevant protected native verifier passes; otherwise `FAIL`. Environment/setup failures before model scoring are `INFRASTRUCTURE_FAILURE`.

Each cell records the fields in `cp3/RESULT_SCHEMA.json`, plus matched activation terms, sanitized-input hash, model-output hashes, edit hashes, timing, and infrastructure details.

## Frozen aggregate reporting

Report per-arm pass counts out of all 5 protected cases and explicit activation / false-activation accounting. The pre-existing primary causal comparison remains **ALWAYS_ON vs VERIFIED**. Also report COLD and RAW_MEMORY as descriptive controls.

No significance threshold, minimum win count, or success gate is added after outcomes are observed. The result is reported exactly as obtained.
