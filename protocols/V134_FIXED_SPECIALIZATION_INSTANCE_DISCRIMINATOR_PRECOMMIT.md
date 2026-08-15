# V134 — Fixed specialization before instance synthesis discriminator precommit

Date frozen: 2026-08-16 NZST

## Prior residual

V133 replayed exact admitted K2+K5 on the known real Strata target. The original hidden computed-family-parameter / `Type 1` diagnostic changed, but the target still failed. The new dominant obligations were typeclass requests over symbolic family parameters, including:

- `Arbitrary a_1.mono.base.Metadata`
- `Arbitrary (Identifier a_1.mono.base.IDMeta)`

The direct target itself fixes the relevant Strata family parameter to a concrete monomorphic value. Therefore the next question is whether the derivation pipeline is preserving an unnecessarily generic constructor-local family parameter until instance synthesis instead of specializing it from the already-fixed target.

## Question

When a derivation target fixes an indexed/family parameter to a concrete value, does Specimen still request constructor-field `Arbitrary` instances through a symbolic local family parameter rather than the specialized concrete type?

## Frozen matched discriminator

Create a new controlled family unrelated to Strata after this commit.

### Parameter object

A structure `P` contains one type-valued field `Meta : Type`.

Define a concrete fixed value `P0` with `Meta := Unit`.

### Data/relation family

An inductive data family `Box (p : P)` has a constructor carrying a value of type `p.Meta`.

A relation family `Has {p : P}` witnesses construction of that `Box p` value.

### Two arms

- **GENERIC arm:** derive a producer for arbitrary input `p : P`. This arm is expected to require an `Arbitrary p.Meta`-like capability and may fail without it. It is a control showing that generic generation really does need such evidence.
- **FIXED arm:** derive the same-shaped producer with the target specialized to the concrete `P0`, so the carried field type is definitionally `Unit`. Since an `Arbitrary Unit` instance is available, no symbolic `Arbitrary a.Meta` obligation should remain if specialization is propagated before instance synthesis.

Use exact admitted K2+K5 unchanged. No new repair is allowed in V134.

## Gates

G1 — GENERIC control does not silently become specialized; its diagnostics or generated requirements remain parameter-dependent, or it fails for missing generic field-generation evidence.

G2 — FIXED arm fails under K2+K5 with a symbolic-parameter instance obligation (for example `Arbitrary a.Meta`) despite `P0.Meta = Unit`.

G3 — The FIXED failure is not a universe mismatch, constructor overapplication, or unrelated parser/build error.

G4 — No target-specific Strata name or implementation is used.

Verdict `PASS_V134_SPECIALIZATION_INSTANCE_DISCRIMINATOR` iff G1-G4 hold.

If FIXED passes, verdict `NULL_SPECIALIZATION_PROPAGATES_IN_MINIMAL_CASE`; the Strata residual requires a richer mechanism.

If both arms fail for an unrelated common reason, verdict `INVALID_DISCRIMINATOR`.

## Information-state record

Preserved: the concrete target parameter `P0` and its definitional field `Unit`.

Potentially hidden/lost: the equality/specialization linking constructor-local parameter variables to the fixed target parameter before downstream instance synthesis.

The experiment asks whether that information is present but inaccessible at the point where field-generation evidence is requested (R8 Access) or has been abstracted away by representation (R6 Representation).

## Claim boundary

A pass isolates a specialization/instance-synthesis barrier. It does not justify a repair, does not establish the full Strata mechanism, and does not alter K2/K5 admission.
