import CLC.ContextualBridge

namespace CLC

def behaviorSetoid (A : Form) : Setoid A.State where
  r := ContinuationSafe A
  iseqv := {
    refl := continuationSafe_refl A
    symm := by
      intro x y h
      exact continuationSafe_symm h
    trans := by
      intro x y z hxy hyz
      exact continuationSafe_trans hxy hyz
  }

abbrev Behavior (A : Form) := Quotient (behaviorSetoid A)

def behaviorClass {A : Form} (x : A.State) : Behavior A :=
  Quotient.mk (behaviorSetoid A) x

/-- Every verified transport descends to the behavioral quotient. -/
def behaviorMap
    {A B : Form}
    (a : VerifiedTransport A B) :
    Behavior A → Behavior B :=
  Quotient.lift
    (fun x => Quotient.mk (behaviorSetoid B) (a.mapState x))
    (by
      intro x y h
      exact Quotient.sound (continuationSafe_map h a))

/-- Identity transport acts as identity on behavioral classes. -/
theorem behaviorMap_id (A : Form) :
    behaviorMap (VerifiedTransport.id A) = id := by
  funext q
  exact Quotient.inductionOn q (fun x => rfl)

/-- Behavioral descent respects transport composition. -/
theorem behaviorMap_comp
    {A B D : Form}
    (b : VerifiedTransport B D)
    (a : VerifiedTransport A B) :
    behaviorMap (VerifiedTransport.comp b a) =
      behaviorMap b ∘ behaviorMap a := by
  funext q
  exact Quotient.inductionOn q (fun x => rfl)

end CLC
