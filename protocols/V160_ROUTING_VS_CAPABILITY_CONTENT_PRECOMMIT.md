# V160 — Routing vs Capability Content Precommit

Status: FROZEN BEFORE V160 MODEL OUTCOMES

## Residual inherited from V159

V159 ended `NEGATIVE_V159_ANCESTOR_NOT_CAUSALLY_QUALIFIED` on the prospectively selected natural qualification case `thefuck/32`. Across all three `CANDIDATE_SEMANTIC` seeds, both calls edited `thefuck/rules/apt_get.py`, while the native verifier repeatedly failed `tests/rules/test_ls_lah.py::test_match` with `ls_lah.match(Mock(script='pacman -S binutils'), None)` returning True when False was required.

This licenses a new question only: did failure arise because the acquired capability content was useless, because applicability/routing failed to place that content at the verifier-relevant locus, or because an explicit locus signal alone is sufficient independent of acquired capability semantics?

V159 remains negative. V160 cannot retroactively promote V159.

## Frozen task, model and budget

- Task: BugsInPy `thefuck/32` only.
- BugsInPy repository identity and exact historical runtime: same apparatus as V159.
- Model: `Qwen/Qwen3.5-9B`.
- Seeds: `202608171, 202608172, 202608173`.
- Calls per seed: 2.
- Max tokens per call: 2048.
- Structured-edit protocol, independent fresh checkout per arm/seed, persistent within-cell workspace, source synchronization and full native verifier: unchanged from V159.
- Semantic capability manifest and opaque capability manifest: byte-identical constructions from V159.

## Single manipulated factor: locus signal

The RIGHT locus is derived mechanically from the frozen native failing test identity, not from a reference patch:

`tests/rules/test_ls_lah.py::test_match` -> module under test `thefuck/rules/ls_lah.py`.

The WRONG locus is the equally concrete path repeatedly chosen in V159 and demonstrated not to affect the frozen failing test:

`thefuck/rules/apt_get.py`.

Locus messages are instructions about where to inspect/ground candidate edits, not solution text. No reference patch, fixed-commit diff or protected solution body is exposed.

## Frozen arms

1. `SEM_NONE`: semantic acquired-capability manifest; no additional locus signal.
2. `SEM_RIGHT`: identical semantic manifest plus RIGHT locus signal.
3. `SEM_WRONG`: identical semantic manifest plus WRONG locus signal.
4. `OPAQUE_RIGHT`: V159 length-matched opaque capability manifest plus RIGHT locus signal.
5. `COLD_RIGHT`: no capability manifest plus RIGHT locus signal.

All arms otherwise receive identical task context, native verifier feedback, source synchronization, seeds and budgets.

## Primary endpoint

Native verified solve count (`solved_n`) out of 3.

A capability may be causally qualified for routing-mediated use only if:

- `SEM_RIGHT.solved_n >= 1`, and
- `SEM_RIGHT.solved_n > SEM_WRONG.solved_n`, and
- `SEM_RIGHT.solved_n > SEM_NONE.solved_n`.

This is `PASS_V160_ROUTING_CAUSALLY_RESCUES_SEMANTIC_CAPABILITY` only if, additionally, `SEM_RIGHT.solved_n > max(OPAQUE_RIGHT.solved_n, COLD_RIGHT.solved_n)`.

If RIGHT-locus controls solve as often as `SEM_RIGHT`, the verdict is `V160_LOCUS_SIGNAL_SUFFICIENT_CAPABILITY_SEMANTICS_NOT_NEEDED` and the acquired capability is NOT admitted.

If RIGHT changes routing but no arm solves, the verdict is `OBSTRUCTED_V160_ROUTING_REPAIRED_NO_SEMANTIC_SOLUTION`.

If RIGHT fails to change routing toward `thefuck/rules/ls_lah.py`, the verdict is `NEGATIVE_V160_EXPLICIT_LOCUS_DOES_NOT_REPAIR_ROUTING`.

Infrastructure failures remain R10 and cannot be interpreted scientifically.

## Secondary mechanism endpoints

Prospectively record, but do not substitute for the primary endpoint:

- number of seeds whose first executable edit includes `thefuck/rules/ls_lah.py`;
- number of seeds with any executable edit at that locus;
- transport failures;
- verifier calls and verifier time;
- call-to-solve if solved.

A mechanism endpoint can localize an obstruction but cannot by itself qualify the capability.

## Claim boundary

V160 tests one natural case under a bounded model/budget. A positive result would support a causal interaction between explicit applicability/routing information and the frozen capability representation on this case. It would not establish general continual learning, general developmental accumulation, or downstream compounding. Those require a newly admitted ancestor followed by the already-frozen longitudinal gate on a later natural case.
