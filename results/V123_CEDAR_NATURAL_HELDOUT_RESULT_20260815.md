# V123 — Cedar natural held-out qualification result

**Status:** `CORPUS_CEILING_NO_CEDAR_BINDER_TARGET`

## Frozen target rule

V123 required an existing Cedar `Prop` relation whose output is an inductive family carrying at least one uniform **non-Sort runtime/value parameter**, matching the binder role implicated by V118–V120.

## Post-precommit source inspection

After the protocol was frozen, the pinned `SpecimenTest/CedarExample/Cedar.lean` source was inspected for structurally eligible declarations.

The Cedar world contains many natural inductive relations (`DefinedName`, `WfCedarType`, `WfAttrs`, `WfET`, `LookupEntityAttr`, `GetEntityAttr`, request/environment conversion relations, `SubType`, typing relations, etc.), but their produced values are ordinary unparameterized Cedar datatypes, lists/products whose parameters are types, or explicit relation arguments. The source does not provide the required output family with a uniform non-Sort value parameter analogous to the V118 obstruction.

Therefore no declaration satisfies the frozen V123 structural eligibility rule.

## Verdict

Do not manufacture a Cedar target merely to produce a transfer result. V123 stops at the predeclared corpus ceiling.

This is not evidence against K2. It says only that Cedar is the wrong natural world for this particular binder-role capability.

## Consequence

The final natural held-out capstone still requires a pre-existing source world containing a genuine value-parameterized inductive output family. Strata is known to contain such a family but is not blind because its workaround was already inspected; it may be used only as secondary known-world validation.
