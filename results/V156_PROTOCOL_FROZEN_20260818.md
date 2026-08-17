# V156 First-Loss Control Rescue — Frozen Protocol

Frozen before inspecting any V156 outcome.

Use only the saved V155 step-1 and step-2 checkpoints for the three independent V10 seeds. No weight updates. Same eight held-out strings.

Compare raw exact task performance with two strictly bounded external controls:

1. termination-only: truncate only when the model itself emits the exact target as a prefix; no content editing or synthesis.
2. state-projection: select the exact target only when it already occurs contiguously in the model's emitted trajectory; no character editing or synthesis.

Interpretation:
- termination rescue supports a termination-boundary failure;
- projection rescue without termination rescue supports state-selection/routing failure with target state still emitted inside a longer trajectory;
- neither rescue supports stronger content/access loss under this probe.

Primary causal criterion: frozen-weight improvement on A or AB from raw to either bounded controller while ABC is not degraded by the controller definition.
