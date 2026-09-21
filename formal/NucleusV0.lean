import Std

namespace NucleusV0

/-- Lawful continuations form a right action: doing `a` and then `c`
    is represented by the composite `comp c a`. -/
structure Action (C X : Type) where
  one : C
  comp : C → C → C
  act : C → X → X
  one_act : ∀ x, act one x = x
  comp_act : ∀ c a x, act (comp c a) x = act c (act a x)

/-- Contextual equivalence: every lawful future continuation gives the
    same protected observation. -/
def CtxEq {C X Q V : Type} (A : Action C X) (obs : X → Q → V) (x y : X) : Prop :=
  ∀ c q, obs (A.act c x) q = obs (A.act c y) q

/-- Once equivalence quantifies over all composable futures, lawful
    continuation preserves it automatically. -/
theorem continuationSafe_map
    {C X Q V : Type}
    (A : Action C X)
    (obs : X → Q → V)
    {x y : X}
    (h : CtxEq A obs x y)
    (a : C) :
    CtxEq A obs (A.act a x) (A.act a y) := by
  intro c q
  rw [← A.comp_act c a x, ← A.comp_act c a y]
  exact h (A.comp c a) q

/-- A capability state is its extensional membership predicate.
    This avoids privileging any finite container representation. -/
abbrev Capability (α : Type) := α → Prop

/-- The protected observation language asks, for every named capability,
    whether that capability is present. -/
def CapabilityEq {α : Type} (K L : Capability α) : Prop :=
  ∀ q, K q ↔ L q

/-- Membership-query equivalence is exactly extensional equality of
    capability states. -/
theorem capabilityEq_iff_eq
    {α : Type} (K L : Capability α) :
    CapabilityEq K L ↔ K = L := by
  constructor
  · intro h
    funext q
    exact propext (h q)
  · intro h
    cases h
    intro q
    rfl

/-- A continuation is nonfabricating for a distinction predicate when
    a distinction visible after the step reflects to one before it. -/
def NonFabricating {X : Type} (step : X → X) (D : X → X → Prop) : Prop :=
  ∀ x y, D (step x) (step y) → D x y

/-- Backward attribution is licensed only by an explicit reflection witness. -/
theorem backward_attribution
    {X : Type}
    {step : X → X}
    {D : X → X → Prop}
    (cert : NonFabricating step D)
    {x y : X}
    (post : D (step x) (step y)) :
    D x y :=
  cert x y post

/-- An observation factors through a proposed decomposition only when
    every protected observation can be reconstructed from the factor image. -/
def FactorsThrough {X Y Q V : Type} (F : X → Y) (obs : X → Q → V) : Prop :=
  ∃ obs' : Y → Q → V, ∀ x q, obs x q = obs' (F x) q

/-- A single collision with different protected consequences refutes
    the proposed factorisation. -/
theorem not_factorsThrough_of_collision
    {X Y Q V : Type}
    {F : X → Y}
    {obs : X → Q → V}
    {x y : X}
    {q : Q}
    (sameFactor : F x = F y)
    (differentObs : obs x q ≠ obs y q) :
    ¬ FactorsThrough F obs := by
  intro h
  rcases h with ⟨obs', reconstruct⟩
  apply differentObs
  calc
    obs x q = obs' (F x) q := reconstruct x q
    _ = obs' (F y) q := by rw [sameFactor]
    _ = obs y q := (reconstruct y q).symm

/-- A selector that changes transition semantics must descend through
    consequential equivalence. -/
def EndogenousSelector {X R : Type}
    (eqv : X → X → Prop) (selector : X → R) : Prop :=
  ∀ x y, eqv x y → selector x = selector y


/-! ## AB-like recombination fixture -/

inductive ABState
  | phase0 | phasePi | bright | dark
  deriving DecidableEq, Repr

inductive ABCtx
  | ident | recombine
  deriving DecidableEq, Repr

def ABAct : ABCtx → ABState → ABState
  | .ident, s => s
  | .recombine, .phase0 => .bright
  | .recombine, .phasePi => .dark
  | .recombine, s => s

def ABObs : ABState → Unit → Bool
  | .bright, _ => true
  | _, _ => false

theorem ab_present_equal :
    ABObs (ABAct .ident .phase0) () =
    ABObs (ABAct .ident .phasePi) () := by
  rfl

theorem ab_recombination_separates :
    ABObs (ABAct .recombine .phase0) () ≠
    ABObs (ABAct .recombine .phasePi) () := by
  decide

theorem ab_no_premature_quotient :
    ¬ (∀ (c : ABCtx) (q : Unit),
        ABObs (ABAct c .phase0) q = ABObs (ABAct c .phasePi) q) := by
  intro h
  have bad := h ABCtx.recombine ()
  simp [ABAct, ABObs] at bad


/-! ## Which-path nonfabrication fixture -/

inductive ProbeState
  | latentL | latentR | seenL | seenR
  deriving DecidableEq, Repr

def probe : ProbeState → ProbeState
  | .latentL => .seenL
  | .latentR => .seenR
  | .seenL => .seenL
  | .seenR => .seenR

def PathDist : ProbeState → ProbeState → Prop
  | .seenL, .seenR => True
  | .seenR, .seenL => True
  | _, _ => False

theorem spuriousPath_not_admissible :
    ¬ NonFabricating probe PathDist := by
  intro h
  have post : PathDist (probe .latentL) (probe .latentR) := by
    simp [probe, PathDist]
  have pre := h .latentL .latentR post
  simp [PathDist] at pre


/-! ## Observer-boundary / endogenous-selector fixture -/

def observerAct (_ : Unit) (x : Bool) : Bool := x

def observerObs (_ : Bool) (_ : Unit) : Bool := false

def ObserverEq (x y : Bool) : Prop :=
  ∀ (c : Unit) (q : Unit),
    observerObs (observerAct c x) q =
    observerObs (observerAct c y) q

theorem observerBoundary_equiv : ObserverEq false true := by
  intro c q
  rfl

def externalSelector (x : Bool) : Bool := x

theorem observerBoundary_external_switch_rejected :
    ¬ EndogenousSelector ObserverEq externalSelector := by
  intro h
  have bad := h false true observerBoundary_equiv
  simp [externalSelector] at bad


/-! ## Bell-like factorisation fixture

This is deliberately only a structural factorisation counterexample:
two whole relation states have the same componentwise local-support
summary but different protected joint consequences.
-/

inductive JointRel
  | correlated | anticorrelated
  deriving DecidableEq, Repr

structure LocalSupport where
  leftHas0 : Bool
  leftHas1 : Bool
  rightHas0 : Bool
  rightHas1 : Bool
  deriving DecidableEq, Repr

def localFactor : JointRel → LocalSupport
  | _ => ⟨true, true, true, true⟩

def jointObs : JointRel → Unit → Bool
  | .correlated, _ => true
  | .anticorrelated, _ => false

theorem bellLike_no_component_factorisation :
    ¬ FactorsThrough localFactor jointObs := by
  apply not_factorsThrough_of_collision
      (x := JointRel.correlated)
      (y := JointRel.anticorrelated)
      (q := ())
  · rfl
  · decide

end NucleusV0
