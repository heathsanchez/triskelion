import Nucleus.IndexedContext
import CLC.Transport

namespace CLC

/-- CLC forms and semantically verified transports instantiate the
    heterogeneous contextual nucleus. Protected target tests are the
    query language. -/
def indexedSystem : Nucleus.IndexedContextSystem where
  Obj := Form
  State := fun A => A.State
  Query := fun A => ProtectedTest A
  ObsVal := Verdict
  Hom := fun A B => VerifiedTransport A B
  id := VerifiedTransport.id
  comp := fun b a => VerifiedTransport.comp b a
  mapState := fun a x => a.mapState x
  observe := fun A x p => A.eval x p.1
  map_id := by
    intro A x
    rfl
  map_comp := by
    intro A B D b a x
    rfl

/-- CLC V1 continuation-safe equivalence, stated directly as:
    every verified future transport and every protected target test
    yields the same protected consequence. -/
def ContinuationSafe
    (A : Form)
    (x y : A.State) : Prop :=
  ∀ (B : Form) (a : VerifiedTransport A B) (p : ProtectedTest B),
    B.eval (a.mapState x) p.1 =
    B.eval (a.mapState y) p.1

/-- The decisive adapter theorem: CLC continuation-safe equivalence is
    exactly the generic indexed contextual consequential equivalence. -/
theorem clcEq_iff_indexedCtxEq
    (A : Form)
    (x y : A.State) :
    ContinuationSafe A x y ↔
      Nucleus.CtxEq indexedSystem x y := by
  constructor
  · intro h probe
    exact h probe.target probe.arrow probe.query
  · intro h B a p
    exact h {
      target := B
      arrow := a
      query := p
    }

/-- CLC continuation congruence is an instance of the generic indexed
    contextual congruence theorem. -/
theorem continuationSafe_map
    {A B : Form}
    {x y : A.State}
    (h : ContinuationSafe A x y)
    (a : VerifiedTransport A B) :
    ContinuationSafe B (a.mapState x) (a.mapState y) := by
  have hk : Nucleus.CtxEq indexedSystem x y :=
    (clcEq_iff_indexedCtxEq A x y).mp h
  have hm := Nucleus.continuationSafe_map indexedSystem hk a
  exact (clcEq_iff_indexedCtxEq B (a.mapState x) (a.mapState y)).mpr hm

theorem continuationSafe_refl
    (A : Form)
    (x : A.State) :
    ContinuationSafe A x x := by
  exact (clcEq_iff_indexedCtxEq A x x).mpr
    (Nucleus.ctxEq_refl indexedSystem x)

theorem continuationSafe_symm
    {A : Form}
    {x y : A.State}
    (h : ContinuationSafe A x y) :
    ContinuationSafe A y x := by
  have hk := (clcEq_iff_indexedCtxEq A x y).mp h
  exact (clcEq_iff_indexedCtxEq A y x).mpr
    (Nucleus.ctxEq_symm indexedSystem hk)

theorem continuationSafe_trans
    {A : Form}
    {x y z : A.State}
    (hxy : ContinuationSafe A x y)
    (hyz : ContinuationSafe A y z) :
    ContinuationSafe A x z := by
  have hkxy := (clcEq_iff_indexedCtxEq A x y).mp hxy
  have hkyz := (clcEq_iff_indexedCtxEq A y z).mp hyz
  exact (clcEq_iff_indexedCtxEq A x z).mpr
    (Nucleus.ctxEq_trans indexedSystem hkxy hkyz)

end CLC
