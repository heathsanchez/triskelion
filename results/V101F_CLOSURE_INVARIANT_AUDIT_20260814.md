# V101F Structural Closure-Invariant Audit — POST-HOC / NONCLAIM

Date: 2026-08-14 NZST

Purpose: after V101P showed that depth-2 lawful composition solves `sieve` but not `breadth_first_search`, `subsequences`, or `find_in_sorted`, ask whether the remaining three residuals are merely deeper-search failures or are structurally outside the unbounded closure of the current balanced constructor families.

This audit is post-hoc because the independently authored correct implementations for these four V100P tasks were opened after the frozen diagnostic. It cannot count as fresh external evidence. It is used only to characterize the expressivity of K and design a fresh-split successor.

## Current generic mutation families

The V100 balanced constructor allocates over the same underlying families as V98/V99:

- `NAME_SUB`: replace an existing `Name` identifier by another identifier already present in the source;
- `CONST_SUB`: replace an existing scalar constant by another scalar constant from the fixed set;
- `CMP_OP`: relabel an existing comparison operator;
- `BIN_OP`: relabel an existing binary operator;
- `BOOL_OP`: relabel an existing boolean operator;
- `CALL_ARG_SWAP`: permute existing call arguments;
- `CALL_ARG_NAME`: replace a call argument that is already a `Name` by another existing `Name`;
- `NEGATE_GUARD`: wrap an existing `if`/`while` test in unary `not`;
- `STATE_UPDATE_INSERT`: insert the specific form `existing_set.add(existing_name)` before a return when an `.add` receiver already exists.

Balancing changes allocation across these families; it does not change their semantics.

## Closure invariants

### I1 — identifier-vocabulary preservation

Apart from the fixed attribute token introduced by the special state-update insertion, the families do not synthesize an arbitrary new callable identifier. `NAME_SUB` and `CALL_ARG_NAME` choose only among names already present in the source.

Therefore repeated composition cannot in general introduce a missing builtin such as `all` if it is absent from the original identifier vocabulary.

This is why V101P's `sieve` result is important: the target does **not** require inventing `all`; the old closure instead finds an extensionally adequate composition using existing comparison/negation machinery. The apparent missing callable is therefore not a genuine obstruction for that task.

### I2 — guard-root restriction

For a guard whose root is a scalar `Constant`, the existing local families can relabel the constant and repeatedly wrap it in `UnaryOp(Not, ...)`, but no family replaces that guard root with an arbitrary in-scope `Name` expression.

Hence a target shape such as `while True -> while queue` is outside this constructor closure at that site.

### I3 — call-argument root restriction

For a call argument whose root is `Name`, the existing call-argument families can replace it with another existing `Name` or swap it with another existing argument. `BIN_OP` can only relabel an already-existing `BinOp`; it does not construct a new `BinOp` around a `Name`.

Hence a target shape such as `mid -> mid + 1` at a recursive call argument is outside this constructor closure.

### I4 — list-nesting restriction

No existing family increases literal list nesting depth at a return value. Scalar constant substitution does not apply to list structure; operator/name relabelling preserves the list constructor topology; state-update insertion changes statement structure rather than the returned list literal.

Hence `return [] -> return [[]]` is outside this constructor closure.

## Consequence

V101P establishes empirically that one V100P obstruction (`sieve`) disappears under depth-2 closure. This audit explains why the other three are qualitatively different:

- `breadth_first_search`: needs expression-root construction at a guard;
- `find_in_sorted`: needs expression-tree growth at a call argument;
- `subsequences`: needs structural value construction.

These are instances of one broader missing capability class:

`typed expression / value construction at an operational slot`.

The relevant next experiment must use a fresh split excluding all four post-hoc inspected tasks. It should add a generic expression-construction substrate rather than the three specific human repairs, and ask whether that substrate strictly expands external closure. V102 is that bridge.

## Claim boundary

This audit does **not** establish that typed expression construction is autonomously discovered, minimal, universal, or the next cognitive primitive. It establishes only a structural obstruction of the current K and motivates a fresh-split test of a more expressive generic constructor class.
