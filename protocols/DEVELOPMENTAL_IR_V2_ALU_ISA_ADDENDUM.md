# DEVELOPMENTAL IR V2 — pre-outcome implementation addendum

Status: **FROZEN BEFORE EXECUTION**

This note resolves one control wording ambiguity in the precommit without changing any gate threshold.

For F15/F16, `RANDOM32` is implemented as an **equal-size low-reuse ablation control**:

- ABLATE_TOP32 removes the 32 most reused capabilities from the otherwise full frozen Phase-5 archive.
- RANDOM32 removes 32 age-matched low-reuse capabilities from the otherwise full frozen Phase-5 archive.

Thus both controls remove exactly 32 capabilities. F16 is evaluated as:

[
Delta C_{mathrm{RANDOM32}} < 	frac12Delta C_{mathrm{TOP32}}.
]

This is the intended archive-size control: if the learned ISA has concentrated utility, removing the high-reuse instructions should hurt materially more than removing 32 ordinary instructions.
