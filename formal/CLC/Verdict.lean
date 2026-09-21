namespace CLC

inductive Verdict where
  | unknown
  | eq
  | dist
  deriving DecidableEq, Repr

/-- Flat information refinement: UNKNOWN may refine to either decisive
    verdict; decisive verdicts refine only to themselves. -/
def Refines : Verdict → Verdict → Prop
  | .unknown, _ => True
  | .eq, .eq => True
  | .dist, .dist => True
  | _, _ => False

theorem refines_refl (v : Verdict) : Refines v v := by
  cases v <;> trivial

theorem refines_trans {a b c : Verdict}
    (hab : Refines a b)
    (hbc : Refines b c) :
    Refines a c := by
  cases a <;> cases b <;> cases c <;> simp [Refines] at hab hbc ⊢

theorem decisive_preserved_eq {v : Verdict}
    (h : Refines .eq v) :
    v = .eq := by
  cases v <;> simp [Refines] at h ⊢

theorem decisive_preserved_dist {v : Verdict}
    (h : Refines .dist v) :
    v = .dist := by
  cases v <;> simp [Refines] at h ⊢

end CLC
