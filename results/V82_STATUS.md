# V82 Status

**Verdict: `PASS_IVAG_CALIBRATION_V82`**

Boundary: bounded external-function IVAG calibration. External callable semantics are independently authored; the typed task interfaces, dependency classes, and low-level synthesis grammars are authored. This does **not** close the natural heterogeneous IVAG crown-jewel claim.

Primary CI:
- branch: `v82-ivag`
- run: `31778861939`
- head: `acfb2d2864baf3182dee6c5fca8186a8f52d84c0`
- artifact: `9210908694`
- artifact SHA-256: `2d8fdd09cf5fdae39694f9c49cb28490ac37d8088cda78d38904e075502c194a`
- vendored result: `results/attested/V82_IVAG_CALIBRATION_RESULT.json`

Both independent source curricula induced the same three extensional extension classes:
1. `CALL_PORT -> RECORD` (Evidence, DL=2)
2. `SIM_ALL -> MATCH -> FILTER` (Relation/selection, DL=3)
3. `APPLY_STEP -> CHECK_STABLE -> LOOP_BACK` (Control/fixed-point, DL=3)

For both streams the frozen held-out closure frontier grew strictly and conservatively:

`0 -> 16 -> 30 -> 33`

All frozen gates passed: strict closure growth, minimum-description extensions, conservativity, E1 descendant counterfactual, E2->E3 counterfactual, independent quotient convergence, and matched-DL advantage.

The next scientific gate is the same IVAG controller on pre-existing heterogeneous external tasks whose dependency structure was not authored for the experiment.
