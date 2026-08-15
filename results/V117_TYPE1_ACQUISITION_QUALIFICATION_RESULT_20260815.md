# V117 — Type-1 acquisition qualification result

**Hosted run:** `heathsanchez/specimen` Actions run `31879874641`

**Artifact:** `v117-type1-acquisition`

**Artifact digest:** `sha256:f5eb67019cb7c9be1eb3e460d1ef5e5f4da736c14b81ec67f1a38941486ca6ee`

## Verdict

`NULL_WRONG_OBSTRUCTION / QUALIFICATION_FAILED`

The frozen V117 hypothesis predicted a matched lower-universe control would be constructible while the analogous higher-universe structure-parameter case would fail.

Observed:

- lower-universe control: `rc = 1`
- higher-universe acquisition: `rc = 1`

Both fail with the same constructor-emission error:

`Function expected at V117*Expr.unit ... Expected a function because this term is being applied to the argument a_1`

Therefore the qualified obstruction is **not specifically higher-universe / Type-1**.

## What the failure reveals

The residual points to a broader distinction: the deriver is emitting a fixed inductive **parameter** as though it were an ordinary explicit constructor argument. The same failure occurs when the parameter's structure lives in ordinary `Type`.

This falsifies the V117 framing:

`HIGHER_UNIVERSE_PARAMETER` is too narrow.

A successor must distinguish at least:

- fixed implicit/uniform inductive parameters;
- explicit constructor/index arguments;

and test whether preserving that distinction changes constructibility.

## Scientific handling

No K1 patch is admitted under V117. The protocol stops at qualification failure. The result is retained as a negative because it changes the representation of the obstruction before implementation work begins.
