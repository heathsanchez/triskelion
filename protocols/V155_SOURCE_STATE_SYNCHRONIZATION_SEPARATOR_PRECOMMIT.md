# V155 SOURCE-STATE SYNCHRONIZATION SEPARATOR — PRECOMMIT

Purpose: V154 preserved the post-call-1 workspace, but V154B found 39/39 recoverable call-2 alternatives were grounded in the original clean source and 0/39 in the actual post-call-1 source.

Frozen question: if call 2 is shown the exact current post-call-1 source around the changed region, does raw T1 or compiled O1 improve T2 repair relative to the same controls?

Everything from V154 stays fixed: task, provider/model, provider dependency, five arms, three seeds, two-call budget, token budget, structured edits, three-rival schema, deterministic first-valid-distinct selection, historical verifier/runtime, persistent workspace, advantage calculation, and protected evaluation boundary.

Sole intervention: after call 1 is applied and fails the native verifier, append CURRENT SOURCE STATE. For each call-1 changed file, use `git diff --unified=0` only to identify current-side hunk line numbers, then read the CURRENT file and expose merged windows from 40 lines before through 40 lines after each hunk. Prefix current line numbers and include SHA256 of the complete current file. Never show the diff body or deleted/original source text. If no current-side hunk can be reconstructed, return R10. Tell call 2 that every `old` string must occur exactly once in the CURRENT source shown.

Frozen synchronization gate: selected call-2 rivals must reach the native verifier on at least 2/3 seeds in EACH critical arm: D_COLD, D_PLUS_RAW_T1, D_PLUS_SHAM_RAW.

Frozen interpretation hierarchy:
1. snapshot failure -> R10_INCONCLUSIVE_V155_SOURCE_SNAPSHOT
2. comparability failure -> R10_INCONCLUSIVE_V155
3. sync gate fails -> OBSTRUCTED_V155_SOURCE_SYNC_DID_NOT_RESTORE_EXECUTION
4. sync passes + raw and compiled positive -> PASS_V155_BOTH_REPRESENTATIONS_SIGNAL_AFTER_SOURCE_SYNC
5. sync passes + compiled positive -> PASS_V155_COMPILED_O1_SIGNAL_AFTER_SOURCE_SYNC
6. sync passes + raw positive -> PASS_V155_RAW_T1_SIGNAL_AFTER_SOURCE_SYNC
7. sync passes + neither positive -> NEGATIVE_V155_NO_T1_DEVELOPMENTAL_SIGNAL_AFTER_SOURCE_SYNC

Positive advantage remains exactly REACHABILITY or EFFICIENCY.

Protocol, runner, and workflow are committed before outcomes. Window locations are mechanically determined from the executed call-1 edit; no outcome-dependent task, seed, arm, or window selection is permitted.
