import CLC.Verdict

namespace CLC

/-- Minimal semantic CLC form.  The certificate/authority layer is
    intentionally not included in this first adapter slice. -/
structure Form where
  State : Type
  Test : Type
  protected : Test → Prop
  eval : State → Test → Verdict

abbrev ProtectedTest (A : Form) := {p : A.Test // A.protected p}

end CLC
