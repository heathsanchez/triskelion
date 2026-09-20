# Developmental IR V0 — Transparent Verified Capability Runtime

Status: prototype engineering branch built from the V1–V7 experimental lineage.

## Design correction from V7

A promoted capability is **not** treated as an opaque one-cycle CPU instruction.

The native reality check showed that opaque calls can block whole-program optimization badly, while transparent inline capabilities preserved optimization, reduced source size, and compiled faster on the tested workload.

Therefore the V0 rule is:

[
oxed{	extbf{Capabilities are verified, named, reusable, but always re-expandable.}}
]

A capability is an optimization / development unit, not a new trusted semantic primitive.

## Kernel term language

[
t ::= mathbf{1}mid x_imid D(t,t)mid C_j(t_1,ldots,t_k)
]

where

[
D(a,b)=
eg aland b.
]

The trusted semantics of a capability call is its verified D+GROUND expansion.

## Capability certificate

Each capability stores:

- `id`
- `arity`
- exact truth table
- transparent D+GROUND expansion
- verifier digest
- provenance / admission metadata
- optional utility / reuse metadata

Admission is lawful only if exhaustive verification over all (2^k) argument rows proves that the expansion exactly denotes the stored truth table.

## Compiler contract

The compiler may:

- leave a capability call symbolic for development / analysis;
- inline its certified expansion;
- lower it to a backend-specific intrinsic only when that intrinsic is separately known equivalent;
- hash-cons / quotient equivalent certified consequences;
- profile reuse and change inlining policy.

The compiler may **not** treat a capability name as semantically authoritative by itself.

## Developmental archive

The archive is budgetable.

For schema (f):

[
U_f=n_fmax(c_f-1,0)
]

is one simple online utility signal, where (n_f) is observed reuse and (c_f) is transparent expansion cost.

Promotion, retention, and eviction are policy decisions above the trusted kernel.

## External warrant

Verification remains outside the developmental nucleus.

A proposal may be generated internally but must not self-certify.

## V0 backend policy

Default native lowering is **transparent inline**.

Opaque / noinline lowering is an explicit opt-in backend decision justified by measured code-size or runtime tradeoffs.

## Claim boundary

This prototype is a small executable IR and certificate runtime. It is not a production compiler, not a new hardware ISA, and not a claim of general autonomous intelligence.

The experimentally supported bounded architecture is:

[
oxed{
	ext{D+GROUND}
	o
	ext{verified parametric capability}
	o
	ext{utility-driven language growth}
	o
	ext{transparent native lowering}
}
]
