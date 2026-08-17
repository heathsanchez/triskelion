# V161A — State-Aligned Binding Replay Precommit

## Question
V161 binding arms emitted edits whose `old` source corresponds to the post-first-repair state, while V161 applied them to the clean buggy state. Does state alignment alone make those frozen binding candidates executable and/or verified?

## Status
Diagnostic-only, zero model calls. This experiment cannot upgrade V161 into a developmental PASS. It can only classify the V161 residual.

## Frozen source evidence
Task: `thefuck/32`.

Post-first-repair transition, observed in V160/V161 semantic no-binding arm:

```json
{"edits":[{"path":"thefuck/rules/ls_lah.py","old":"def match(command, settings):\n    return 'ls' in command.script","new":"def match(command, settings):\n    return 'ls' in command.script and '-lah' not in command.script"}]}
```

Frozen right-binding candidate observed identically for all three V161 seeds:

```json
{"edits":[{"path":"thefuck/rules/ls_lah.py","old":"def match(command, settings):\n    return 'ls' in command.script and '-lah' not in command.script","new":"def match(command, settings):\n    return command.script.startswith('ls ') and '-lah' not in command.script"}]}
```

Frozen wrong-binding candidate observed identically for all three V161 seeds:

```json
{"edits":[{"path":"thefuck/rules/ls_lah.py","old":"def match(command, settings):\n    return 'ls' in command.script and '-lah' not in command.script","new":"def match(command, settings):\n    return 'ls' in command.script and '-lah' not in command.script and 'pacman' not in command.script"}]}
```

## Apparatus
- BugsInPy HEAD must equal `11c5f1eea954a42132cfd06bf257766a7963e0fd`.
- Exact historical verifier only.
- Fresh checkout per replay.
- No precompiled/cached candidate templates.
- No model/provider calls.

## Decision rule
1. If the first repair cannot apply or fails apparatus identity: `R10_V161A_REPLAY_INVALID`.
2. If the right-binding candidate applies on post-first state and reaches the native verifier, while it could not apply on clean state in V161: `DIAGNOSTIC_V161_STATE_ALIGNMENT_CONFIRMED`.
3. If the right-binding candidate additionally passes the native verifier: `DIAGNOSTIC_V161_STATE_ALIGNED_RIGHT_BIND_VERIFIED`.
4. If right-binding still cannot apply on post-first state: `DIAGNOSTIC_V161_BINDING_CANDIDATE_UNGROUNDED`.
5. Wrong-binding outcome is secondary and cannot alter the primary classification.

No downstream developmental claim is licensed by this diagnostic.