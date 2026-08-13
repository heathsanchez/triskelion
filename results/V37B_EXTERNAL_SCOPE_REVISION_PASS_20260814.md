# V37b External Scope Revision — PASS

Run: 31734286417
Commit: d8ac61f8fcb04dc1236317389b04bf440c0cc71a
Protocol seed: `V37B_EXTERNAL_SCOPE_REVISION_20260814`

The frozen V37b mechanism was run unchanged after expanding only the fixed external repository pool from five to eight independently authored repositories.

Repositories: Requests, Flask, Rich, Click, HTTPX, pytest, Pydantic, Django, all pinned to explicit commits.

Deterministic selected direction: `LT_TO_LTE` (`REPAIR_Lt_TO_LtE`).

Deterministic source-distinct roles:
- train positive: pytest
- train protected: Rich
- held positive: Django
- held protected: Pydantic
- contradiction: Click

Raw role support before capped selection: `[17, 22, 35, 61, 16]`.
Selected evaluation counts: train positive 8; train protected 8; held positive 12; held protected 12; contradictions 8. Total eligible function pool: 552.

Scope search:
- `ANY`: positives 8/8; protected 0/8
- `IF_TEST`: positives 8/8; protected 8/8
- all other supplied structural scopes failed to repair the positives

`IF_TEST` was therefore the unique surviving scoped rule.

Source-distinct held-out evaluation:
- scoped `IF_TEST`: positive 12/12; protected 12/12
- fossilized `ANY`: positive 12/12; protected 0/12

Later independently authored Click evidence supplied 8/8 contradictions to the retained `IF_TEST` rule. The frozen revision policy returned `REVOKE`.

All gates passed:
1. adequate external examples
2. old state fails mutated trigger cases
3. provisional unscoped rule repairs all triggers
4. unscoped rule corrupts external valid code
5. unique scope discovered
6. scope transfers to source-distinct held-out code
7. revision ablation fossilizes bad rule
8. new external counterevidence falsifies retained scope
9. system revokes falsified scope

Verdict: `PASS_EXTERNAL_SCOPE_REVISION_V37B`.

Claim boundary: correctness authority remains exact AST restoration/preservation against independently authored source-of-truth. This is not yet repository-test-backed semantic correctness under execution.
