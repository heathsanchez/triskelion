namespace Nucleus

/-- A heterogeneous continuation system. Objects may have different state
    and query types. Lawful arrows compose, and each arrow maps source
    states into target states. -/
structure IndexedContextSystem where
  Obj : Type
  State : Obj → Type
  Query : Obj → Type
  ObsVal : Type
  Hom : Obj → Obj → Type
  id : (A : Obj) → Hom A A
  comp : {A B D : Obj} → Hom B D → Hom A B → Hom A D
  mapState : {A B : Obj} → Hom A B → State A → State B
  observe : (A : Obj) → State A → Query A → ObsVal
  map_id : ∀ {A} (x : State A), mapState (id A) x = x
  map_comp : ∀ {A B D} (b : Hom B D) (a : Hom A B) (x : State A),
    mapState (comp b a) x = mapState b (mapState a x)

/-- A probe from A consists of a lawful future continuation to some
    target B together with one protected observation at B. -/
structure Probe (S : IndexedContextSystem) (A : S.Obj) where
  target : S.Obj
  arrow : S.Hom A target
  query : S.Query target

def probeObserve
    (S : IndexedContextSystem)
    {A : S.Obj}
    (x : S.State A)
    (p : Probe S A) : S.ObsVal :=
  S.observe p.target (S.mapState p.arrow x) p.query

/-- Heterogeneous contextual consequential equivalence. -/
def CtxEq
    (S : IndexedContextSystem)
    {A : S.Obj}
    (x y : S.State A) : Prop :=
  ∀ p : Probe S A, probeObserve S x p = probeObserve S y p

theorem ctxEq_refl
    (S : IndexedContextSystem)
    {A : S.Obj}
    (x : S.State A) :
    CtxEq S x x := by
  intro p
  rfl

theorem ctxEq_symm
    (S : IndexedContextSystem)
    {A : S.Obj}
    {x y : S.State A}
    (h : CtxEq S x y) :
    CtxEq S y x := by
  intro p
  exact (h p).symm

theorem ctxEq_trans
    (S : IndexedContextSystem)
    {A : S.Obj}
    {x y z : S.State A}
    (hxy : CtxEq S x y)
    (hyz : CtxEq S y z) :
    CtxEq S x z := by
  intro p
  exact (hxy p).trans (hyz p)

/-- The indexed version of continuationSafe_map.  It is forced by
    quantification over every composable future probe. -/
theorem continuationSafe_map
    (S : IndexedContextSystem)
    {A B : S.Obj}
    {x y : S.State A}
    (h : CtxEq S x y)
    (a : S.Hom A B) :
    CtxEq S (S.mapState a x) (S.mapState a y) := by
  intro p
  let lifted : Probe S A := {
    target := p.target
    arrow := S.comp p.arrow a
    query := p.query
  }
  have hp := h lifted
  simpa [probeObserve, lifted, S.map_comp] using hp

end Nucleus
