import CLC.Reversibility

namespace CLC.Fixtures

def boolEval (x q : Bool) : Verdict :=
  if x = q then .eq else .dist

def BoolForm : Form where
  State := Bool
  Test := Bool
  protected := fun _ => True
  eval := boolEval

inductive Tagged where
  | zero
  | one
  deriving DecidableEq, Repr

def encode : Bool → Tagged
  | false => .zero
  | true => .one

def decode : Tagged → Bool
  | .zero => false
  | .one => true

def taggedEval (x q : Tagged) : Verdict :=
  if x = q then .eq else .dist

def TaggedForm : Form where
  State := Tagged
  Test := Tagged
  protected := fun _ => True
  eval := taggedEval

def encodeTransport : VerifiedTransport BoolForm TaggedForm where
  mapState := encode
  pullTest := decode
  liftProtect := fun p => ⟨encode p.1, trivial⟩
  pullProtected := by
    intro d hd
    trivial
  refine := by
    intro x d
    cases x <;> cases d <;> simp [BoolForm, TaggedForm, boolEval, taggedEval, encode, decode, Refines]
  split := by
    intro p
    rcases p with ⟨p, hp⟩
    cases p <;> rfl

def decodeTransport : VerifiedTransport TaggedForm BoolForm where
  mapState := decode
  pullTest := encode
  liftProtect := fun p => ⟨decode p.1, trivial⟩
  pullProtected := by
    intro d hd
    trivial
  refine := by
    intro x d
    cases x <;> cases d <;> simp [BoolForm, TaggedForm, boolEval, taggedEval, encode, decode, Refines]
  split := by
    intro p
    rcases p with ⟨p, hp⟩
    cases p <;> rfl

theorem encode_decode_behavioral_inverse :
    BehavioralInverse encodeTransport decodeTransport := by
  constructor
  · intro x
    cases x <;>
      simpa [encodeTransport, decodeTransport, encode, decode] using
        (continuationSafe_refl BoolForm (x := false))
  · intro y
    cases y <;>
      simpa [encodeTransport, decodeTransport, encode, decode] using
        (continuationSafe_refl TaggedForm (x := Tagged.zero))

/-- Positive fixture: different forms induce genuinely inverse maps on
    their behavioral quotients. -/
def encode_decode_behavior_equiv :
    Behavior BoolForm ≃ Behavior TaggedForm :=
  behaviorEquiv encodeTransport decodeTransport
    encode_decode_behavioral_inverse

def flipBool : Bool → Bool
  | false => true
  | true => false

def flipTransport : VerifiedTransport BoolForm BoolForm where
  mapState := flipBool
  pullTest := flipBool
  liftProtect := fun p => ⟨flipBool p.1, trivial⟩
  pullProtected := by
    intro d hd
    trivial
  refine := by
    intro x d
    cases x <;> cases d <;>
      simp [BoolForm, boolEval, flipBool, Refines]
  split := by
    intro p
    rcases p with ⟨p, hp⟩
    cases p <;> rfl

theorem flip_has_residual :
    HasResidualAt
      flipTransport
      false
      BoolForm
      (VerifiedTransport.id BoolForm)
      (⟨false, trivial⟩ : ProtectedTest BoolForm) := by
  simp [HasResidualAt, flipTransport, VerifiedTransport.id,
    BoolForm, boolEval, flipBool]

/-- Negative fixture: returning to the same form is not enough.  The
    loop is a lawful transport but is not continuation-neutral because
    the identity future probe exposes a protected residual. -/
theorem same_form_not_behaviorally_reversible :
    ¬ ContinuationNeutral flipTransport := by
  intro h
  have hn := (continuationNeutral_iff_noResidual flipTransport).mp h
  exact hn false BoolForm (VerifiedTransport.id BoolForm)
    (⟨false, trivial⟩ : ProtectedTest BoolForm) flip_has_residual

end CLC.Fixtures
