import CLC.Form

namespace CLC

/-- A semantically verified developmental transport.  This is the
    semantic core of the CLC V1 transport record: forward state map,
    contravariant test map, protected-test lift, refinement law, and
    split law.  Certificate checking is a later layer. -/
structure VerifiedTransport (A B : Form) where
  mapState : A.State → B.State
  pullTest : B.Test → A.Test
  liftProtect : ProtectedTest A → ProtectedTest B
  pullProtected : ∀ d : B.Test, B.isProtected d → A.isProtected (pullTest d)
  refine : ∀ (x : A.State) (d : B.Test),
    Refines (A.eval x (pullTest d)) (B.eval (mapState x) d)
  split : ∀ p : ProtectedTest A,
    pullTest (liftProtect p).1 = p.1

def VerifiedTransport.id (A : Form) : VerifiedTransport A A where
  mapState := id
  pullTest := id
  liftProtect := id
  pullProtected := by
    intro d hd
    exact hd
  refine := by
    intro x d
    exact refines_refl _
  split := by
    intro p
    rfl

def VerifiedTransport.comp
    {A B D : Form}
    (b : VerifiedTransport B D)
    (a : VerifiedTransport A B) :
    VerifiedTransport A D where
  mapState := fun x => b.mapState (a.mapState x)
  pullTest := fun d => a.pullTest (b.pullTest d)
  liftProtect := fun p => b.liftProtect (a.liftProtect p)
  pullProtected := by
    intro d hd
    exact a.pullProtected (b.pullTest d) (b.pullProtected d hd)
  refine := by
    intro x d
    exact refines_trans
      (a.refine x (b.pullTest d))
      (b.refine (a.mapState x) d)
  split := by
    intro p
    calc
      a.pullTest (b.pullTest (b.liftProtect (a.liftProtect p)).1)
          = a.pullTest (a.liftProtect p).1 := by
              rw [b.split (a.liftProtect p)]
      _ = p.1 := a.split p

theorem VerifiedTransport.id_mapState
    (A : Form) (x : A.State) :
    (VerifiedTransport.id A).mapState x = x := by
  rfl

theorem VerifiedTransport.comp_mapState
    {A B D : Form}
    (b : VerifiedTransport B D)
    (a : VerifiedTransport A B)
    (x : A.State) :
    (VerifiedTransport.comp b a).mapState x =
      b.mapState (a.mapState x) := by
  rfl

end CLC
