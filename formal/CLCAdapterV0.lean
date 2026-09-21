import NucleusV0

namespace NucleusV0

/-- Generic extensional equality under a declared family of contexts.
    This is the heterogeneous adapter surface used by CLC: the context
    itself carries whatever typed continuation is needed. -/
def ContextualObsEq {X K V : Type}
    (obs : X → K → V) (x y : X) : Prop :=
  ∀ k, obs x k = obs y k

end NucleusV0

namespace CLCV0

/-! ## Verdicts -/

inductive Verdict
  | unknown
  | eq
  | dist
  deriving DecidableEq, Repr

def Verdict.le : Verdict → Verdict → Prop
  | .unknown, _ => True
  | .eq, .eq => True
  | .dist, .dist => True
  | _, _ => False

instance : LE Verdict := ⟨Verdict.le⟩

theorem verdict_le_refl (v : Verdict) : v ≤ v := by
  cases v <;> trivial

theorem verdict_le_trans {u v w : Verdict} (huv : u ≤ v) (hvw : v ≤ w) : u ≤ w := by
  cases u <;> cases v <;> cases w <;> simp_all [Verdict.le]

def Decisive (v : Verdict) : Prop := v = .eq ∨ v = .dist

theorem unknown_le (v : Verdict) : Verdict.unknown ≤ v := by
  cases v <;> trivial

theorem decisive_eq_of_le {v w : Verdict}
    (hv : Decisive v) (hvw : v ≤ w) : w = v := by
  rcases hv with rfl | rfl <;> cases w <;> simp_all [Verdict.le, Decisive]

/-! ## CLC forms and verified transports

This is the first semantic adapter slice of the CLC V1 contract:
finite state/test carriers, protected tests, forward state transport,
backward test transport, protected lifting, refinement, and split.
Certificate authority is intentionally minimal here; richer provenance,
revocation, and policy semantics remain outside this V0 bridge.
-/

structure Form where
  State : Type
  Test : Type
  stateFinite : Fintype State
  testFinite : Fintype Test
  decState : DecidableEq State
  decTest : DecidableEq Test
  protected : Test → Bool
  eval : State → Test → Verdict

attribute [instance] Form.stateFinite Form.testFinite Form.decState Form.decTest

def Protected (A : Form) := {p : A.Test // A.protected p = true}

structure AuthoritySnapshot (Cert : Type) where
  accepts : Cert → Bool
  live : Cert → Bool
  idCert : Cert
  compCert : Cert → Cert → Cert
  accepts_id : accepts idCert = true
  live_id : live idCert = true
  accepts_comp :
    ∀ {a b}, accepts a = true → accepts b = true → accepts (compCert a b) = true
  live_comp :
    ∀ {a b}, live a = true → live b = true → live (compCert a b) = true

structure TransportData (Cert : Type) (A B : Form) where
  mapState : A.State → B.State
  pullTest : B.Test → A.Test
  pullProtected : ∀ d, B.protected d = true → A.protected (pullTest d) = true
  liftProtected : Protected A → Protected B
  refine : ∀ x d, A.eval x (pullTest d) ≤ B.eval (mapState x) d
  split : ∀ p, pullTest (liftProtected p).1 = p.1
  cert : Cert

structure VerifiedTransport {Cert : Type}
    (Ω : AuthoritySnapshot Cert) (A B : Form)
    extends TransportData Cert A B where
  checked : Ω.accepts cert = true
  liveAt : Ω.live cert = true

namespace VerifiedTransport

def id {Cert : Type} (Ω : AuthoritySnapshot Cert) (A : Form) :
    VerifiedTransport Ω A A where
  mapState := fun x => x
  pullTest := fun d => d
  pullProtected := by
    intro d hd
    exact hd
  liftProtected := fun p => p
  refine := by
    intro x d
    exact verdict_le_refl _
  split := by
    intro p
    rfl
  cert := Ω.idCert
  checked := Ω.accepts_id
  liveAt := Ω.live_id

def comp {Cert : Type} {Ω : AuthoritySnapshot Cert} {A B C : Form}
    (a : VerifiedTransport Ω A B)
    (b : VerifiedTransport Ω B C) :
    VerifiedTransport Ω A C where
  mapState := fun x => b.mapState (a.mapState x)
  pullTest := fun d => a.pullTest (b.pullTest d)
  pullProtected := by
    intro d hd
    exact a.pullProtected (b.pullTest d) (b.pullProtected d hd)
  liftProtected := fun p => b.liftProtected (a.liftProtected p)
  refine := by
    intro x d
    exact verdict_le_trans
      (a.refine x (b.pullTest d))
      (b.refine (a.mapState x) d)
  split := by
    intro p
    change a.pullTest (b.pullTest (b.liftProtected (a.liftProtected p)).1) = p.1
    rw [b.split (a.liftProtected p), a.split p]
  cert := Ω.compCert a.cert b.cert
  checked := Ω.accepts_comp a.checked b.checked
  liveAt := Ω.live_comp a.liveAt b.liveAt

end VerifiedTransport

/-! ## CLC continuation-safe equivalence -/

def ContinuationSafe {Cert : Type}
    (Ω : AuthoritySnapshot Cert) (A : Form)
    (x y : A.State) : Prop :=
  ∀ (B : Form) (a : VerifiedTransport Ω A B) (p : Protected B),
    B.eval (a.mapState x) p.1 = B.eval (a.mapState y) p.1

theorem continuationSafe_refl {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A : Form} {x : A.State} :
    ContinuationSafe Ω A x x := by
  intro B a p
  rfl

theorem continuationSafe_symm {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A : Form} {x y : A.State}
    (h : ContinuationSafe Ω A x y) :
    ContinuationSafe Ω A y x := by
  intro B a p
  exact (h B a p).symm

theorem continuationSafe_trans {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A : Form} {x y z : A.State}
    (hxy : ContinuationSafe Ω A x y)
    (hyz : ContinuationSafe Ω A y z) :
    ContinuationSafe Ω A x z := by
  intro B a p
  exact (hxy B a p).trans (hyz B a p)

theorem continuationSafe_map {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A B : Form}
    (a : VerifiedTransport Ω A B)
    {x y : A.State}
    (hxy : ContinuationSafe Ω A x y) :
    ContinuationSafe Ω B (a.mapState x) (a.mapState y) := by
  intro C b p
  exact hxy C (VerifiedTransport.comp a b) p

/-! ## Adapter: CLC future transports are generic contextual queries -/

structure CLCContext {Cert : Type}
    (Ω : AuthoritySnapshot Cert) (A : Form) where
  target : Form
  transport : VerifiedTransport Ω A target
  test : Protected target

def contextObs {Cert : Type}
    (Ω : AuthoritySnapshot Cert) (A : Form)
    (x : A.State) (k : CLCContext Ω A) : Verdict :=
  k.target.eval (k.transport.mapState x) k.test.1

theorem continuationSafe_iff_contextualKernel {Cert : Type}
    (Ω : AuthoritySnapshot Cert) (A : Form)
    (x y : A.State) :
    ContinuationSafe Ω A x y ↔
      NucleusV0.ContextualObsEq (contextObs Ω A) x y := by
  constructor
  · intro h k
    exact h k.target k.transport k.test
  · intro h B a p
    exact h ⟨B, a, p⟩

/-! ## Behavioral quotient and induced transport -/

def continuationSafeSetoid {Cert : Type}
    (Ω : AuthoritySnapshot Cert) (A : Form) : Setoid A.State where
  r := ContinuationSafe Ω A
  iseqv := {
    refl := fun _ => continuationSafe_refl
    symm := fun h => continuationSafe_symm h
    trans := fun h₁ h₂ => continuationSafe_trans h₁ h₂
  }

abbrev ProtectedBehavior {Cert : Type}
    (Ω : AuthoritySnapshot Cert) (A : Form) :=
  Quotient (continuationSafeSetoid Ω A)

def behaviorMap {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A B : Form}
    (a : VerifiedTransport Ω A B) :
    ProtectedBehavior Ω A → ProtectedBehavior Ω B :=
  Quotient.map a.mapState (by
    intro x y h
    exact continuationSafe_map a h)

theorem behaviorMap_mk {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A B : Form}
    (a : VerifiedTransport Ω A B) (x : A.State) :
    behaviorMap a (Quotient.mk _ x) = Quotient.mk _ (a.mapState x) := by
  rfl

/-! ## Closed-loop residual and behavioral reversibility -/

def ContinuationResidual {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A : Form}
    (loop : VerifiedTransport Ω A A) (x : A.State) : Prop :=
  ∃ (B : Form) (c : VerifiedTransport Ω A B) (p : Protected B),
    B.eval (c.mapState (loop.mapState x)) p.1 ≠
      B.eval (c.mapState x) p.1

def ContinuationNeutral {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A : Form}
    (loop : VerifiedTransport Ω A A) : Prop :=
  ∀ x : A.State, ContinuationSafe Ω A (loop.mapState x) x

theorem continuationNeutral_iff_noResidual {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A : Form}
    (loop : VerifiedTransport Ω A A) :
    ContinuationNeutral loop ↔
      ∀ x : A.State, ¬ ContinuationResidual loop x := by
  constructor
  · intro h x hres
    rcases hres with ⟨B, c, p, hneq⟩
    exact hneq (h x B c p)
  · intro h x B c p
    by_contra hneq
    exact (h x) ⟨B, c, p, hneq⟩

theorem behaviorMap_neutral {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A : Form}
    (loop : VerifiedTransport Ω A A)
    (h : ContinuationNeutral loop) :
    behaviorMap loop = id := by
  funext q
  refine Quotient.inductionOn q ?_
  intro x
  apply Quotient.sound
  exact h x

structure BehavioralInverse {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A B : Form}
    (a : VerifiedTransport Ω A B)
    (r : VerifiedTransport Ω B A) : Prop where
  sourceReturn :
    ∀ x : A.State, ContinuationSafe Ω A (r.mapState (a.mapState x)) x
  targetReturn :
    ∀ y : B.State, ContinuationSafe Ω B (a.mapState (r.mapState y)) y

theorem behaviorMap_inverse_left {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A B : Form}
    (a : VerifiedTransport Ω A B)
    (r : VerifiedTransport Ω B A)
    (h : BehavioralInverse a r) :
    Function.LeftInverse (behaviorMap r) (behaviorMap a) := by
  intro q
  refine Quotient.inductionOn q ?_
  intro x
  apply Quotient.sound
  exact h.sourceReturn x

theorem behaviorMap_inverse_right {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A B : Form}
    (a : VerifiedTransport Ω A B)
    (r : VerifiedTransport Ω B A)
    (h : BehavioralInverse a r) :
    Function.RightInverse (behaviorMap r) (behaviorMap a) := by
  intro q
  refine Quotient.inductionOn q ?_
  intro y
  apply Quotient.sound
  exact h.targetReturn y

theorem behavioralInverse_equiv {Cert : Type}
    {Ω : AuthoritySnapshot Cert} {A B : Form}
    (a : VerifiedTransport Ω A B)
    (r : VerifiedTransport Ω B A)
    (h : BehavioralInverse a r) :
    ∃ e : ProtectedBehavior Ω A ≃ ProtectedBehavior Ω B,
      ∀ q, e q = behaviorMap a q := by
  let e : ProtectedBehavior Ω A ≃ ProtectedBehavior Ω B := {
    toFun := behaviorMap a
    invFun := behaviorMap r
    left_inv := behaviorMap_inverse_left a r h
    right_inv := behaviorMap_inverse_right a r h
  }
  exact ⟨e, by intro q; rfl⟩

/-! ## Minimal positive fixture: raw return is unnecessary -/

def unitSnapshot : AuthoritySnapshot Unit where
  accepts := fun _ => true
  live := fun _ => true
  idCert := ()
  compCert := fun _ _ => ()
  accepts_id := rfl
  live_id := rfl
  accepts_comp := by intros; rfl
  live_comp := by intros; rfl

def opaqueForm : Form where
  State := Bool
  Test := Unit
  stateFinite := inferInstance
  testFinite := inferInstance
  decState := inferInstance
  decTest := inferInstance
  protected := fun _ => true
  eval := fun _ _ => .eq

def flipBool (x : Bool) : Bool := !x

def flipOpaque : VerifiedTransport unitSnapshot opaqueForm opaqueForm where
  mapState := flipBool
  pullTest := fun d => d
  pullProtected := by intros; rfl
  liftProtected := fun _ => ⟨(), rfl⟩
  refine := by
    intro x d
    exact verdict_le_refl _
  split := by
    intro p
    cases p with
    | mk p hp =>
      cases p
      rfl
  cert := ()
  checked := rfl
  liveAt := rfl

theorem opaque_all_continuationSafe (x y : opaqueForm.State) :
    ContinuationSafe unitSnapshot opaqueForm x y := by
  intro B c p
  have hx :
      B.eval (c.mapState x) p.1 = Verdict.eq := by
    exact decisive_eq_of_le (v := Verdict.eq)
      (w := B.eval (c.mapState x) p.1)
      (by exact Or.inl rfl)
      (c.refine x p.1)
  have hy :
      B.eval (c.mapState y) p.1 = Verdict.eq := by
    exact decisive_eq_of_le (v := Verdict.eq)
      (w := B.eval (c.mapState y) p.1)
      (by exact Or.inl rfl)
      (c.refine y p.1)
  exact hx.trans hy.symm

theorem flipOpaque_raw_changes :
    flipOpaque.mapState false ≠ false := by
  decide

def opaqueInverse : VerifiedTransport unitSnapshot opaqueForm opaqueForm :=
  VerifiedTransport.id unitSnapshot opaqueForm

theorem flipOpaque_behavioralInverse :
    BehavioralInverse flipOpaque opaqueInverse := by
  constructor
  · intro x
    exact opaque_all_continuationSafe _ _
  · intro y
    exact opaque_all_continuationSafe _ _

theorem flipOpaque_behavioral_equiv :
    ∃ e : ProtectedBehavior unitSnapshot opaqueForm ≃
        ProtectedBehavior unitSnapshot opaqueForm,
      ∀ q, e q = behaviorMap flipOpaque q :=
  behavioralInverse_equiv flipOpaque opaqueInverse flipOpaque_behavioralInverse

/-! ## Minimal negative fixture: same-form return can leave a residual -/

def latentForm : Form where
  State := Bool
  Test := Unit
  stateFinite := inferInstance
  testFinite := inferInstance
  decState := inferInstance
  decTest := inferInstance
  protected := fun _ => true
  eval := fun _ _ => .unknown

def visibleForm : Form where
  State := Bool
  Test := Unit
  stateFinite := inferInstance
  testFinite := inferInstance
  decState := inferInstance
  decTest := inferInstance
  protected := fun _ => true
  eval := fun x _ => if x then .dist else .eq

def flipLatent : VerifiedTransport unitSnapshot latentForm latentForm where
  mapState := flipBool
  pullTest := fun d => d
  pullProtected := by intros; rfl
  liftProtected := fun _ => ⟨(), rfl⟩
  refine := by
    intro x d
    exact unknown_le _
  split := by
    intro p
    cases p with
    | mk p hp =>
      cases p
      rfl
  cert := ()
  checked := rfl
  liveAt := rfl

def revealLatent : VerifiedTransport unitSnapshot latentForm visibleForm where
  mapState := fun x => x
  pullTest := fun _ => ()
  pullProtected := by intros; rfl
  liftProtected := fun _ => ⟨(), rfl⟩
  refine := by
    intro x d
    exact unknown_le _
  split := by
    intro p
    cases p with
    | mk p hp =>
      cases p
      rfl
  cert := ()
  checked := rfl
  liveAt := rfl

theorem latent_loop_has_residual :
    ContinuationResidual flipLatent false := by
  refine ⟨visibleForm, revealLatent, ⟨(), rfl⟩, ?_⟩
  decide

theorem latent_sameForm_not_neutral :
    ¬ ContinuationNeutral flipLatent := by
  intro h
  have nores := (continuationNeutral_iff_noResidual flipLatent).mp h
  exact (nores false) latent_loop_has_residual

/-! ## Public theorem surface audit -/

#print axioms continuationSafe_map
#print axioms continuationSafe_iff_contextualKernel
#print axioms behaviorMap_neutral
#print axioms behaviorMap_inverse_left
#print axioms behaviorMap_inverse_right
#print axioms behavioralInverse_equiv
#print axioms latent_sameForm_not_neutral

end CLCV0
