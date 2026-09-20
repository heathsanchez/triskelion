# CONSEQUENCE × WHAKAPAPA × FORM V1 — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

Can a developmental system keep three things separate:

1. **Consequence** — the exact protected meaning.
2. **Whakapapa** — the verified causal provenance / dependency graph establishing why the capability is warranted.
3. **Form** — the current executable representation.

and thereby obtain deep ancestry, selective revocation, cross-lineage recombination, and efficient execution at the same time?

Deep Whakapapa V1 established ancestry depth 73 but showed that replaying genealogy as execution can be more expensive than shallow reuse. V7 independently showed that verified capability boundaries should remain transparent to optimization. This experiment tests the resulting architectural correction prospectively.

## Kernel

Trusted primitives remain:

- GROUND = 1
- INPUT
- D(a,b)=not(a) and b
- VERIFY
- PROMOTE

No capability name, provenance edge, or optimized form is trusted by itself.

## Exact carrier

Six independent Boolean inputs, hence 64 exact rows.

Every protected consequence is a complete 64-row truth table.

## Capability record

Each admitted capability C stores three independent fields.

### Consequence

[
K(C)in{0,1}^{64}
]

Exact protected truth table.

Capabilities with identical K are quotient-identical for execution and archive uniqueness.

### Whakapapa

[
W(C)=(parents, verifier digest, admission event)
]

Parents are the verified capabilities used to construct the candidate.

Whakapapa is never erased by optimization.

### Form

[
F(C)
]

A transparent D+GROUND expression implementing K(C).

Form may be replaced by any cheaper transparent expression iff exhaustive verification proves:

[
llbracket F'(C)rbracket=K(C).
]

Replacing form does not alter W(C).

## Founder phase

Episodes 1–2,000 discover at least 16 deterministic verified founder capabilities from expanded D+GROUND structures. No semantic names are used.

## Genealogy phase

Episodes 2,001–14,000.

Each child is constructed from two verified parents using the same sealed family of D/projection constructors as the previous experiment.

Parent selection is modified prospectively to ensure a real recombination test:

- 45% recent-lineage selection;
- 35% full-archive selection;
- 20% explicit **disjoint-lineage mating attempt**.

The disjoint-lineage selector may inspect only ancestry graph intersection, never semantic truth-table identity beyond duplicate rejection.

Children immediately become eligible parents.

## Form optimizer

After a child is verified, independently search a bounded transparent-form candidate set:

1. inherited construction form;
2. exact canonical consequence representative if already known;
3. D expressions synthesized from environmental variables up to cost 12;
4. verified composition forms available from installed capabilities, transparently expanded.

Choose the lowest D-node form, tie-breaking lexicographically by canonical serialization.

The optimizer is allowed to flatten 70 generations of ancestry to a 3-node form if exact verification permits it.

Whakapapa remains unchanged.

## Execution

Execution uses current optimized Form, not ancestry replay.

If a capability is installed, its current form cost is charged.

The genealogy is consulted only for:

- warrant/provenance;
- descendant invalidation;
- recombination policy;
- learning / utility metadata.

## Revocation

At episode 14,001 choose a **reproductively important ancestor**, not a leaf:

1. capability must have at least one descendant;
2. maximize descendant-cone size;
3. then maximize ancestry depth;
4. then lowest capability ID.

Inject counterevidence invalidating its warrant.

Before the next execution:

- revoke target;
- recursively revoke its complete descendant cone;
- preserve all capabilities outside the cone;
- remove their executable forms from the active archive;
- continue development for 3,000 episodes.

## Held-out phase

Episodes 17,001–20,000.

Freeze promotion and form optimization.

Generate unseen reproductive episodes.

## Controls

### GENEALOGY_EXECUTION
Same admitted capabilities and ancestry, but execution cost recursively replays parental construction rather than optimized current Form.

### NO_REENTRY
Children execute but never become parents.

### NO_FORM_OPT
Deep genealogy is enabled but every capability retains its inherited construction form.

### NO_ANCESTRY
Consequence/Form reuse is allowed, but parent edges are discarded. At revocation the system cannot identify descendants.

### RANDOM_MATE
Replace the 20% disjoint-lineage mating attempts with ordinary random parent selection.

### COLD
No persistent capabilities.

## Remove/restore causal probes

At the first time depths 4, 8, 16, and 32 are reached, freeze 100 future episodes.

For each checkpoint:

- full archive execution;
- remove a mid-lineage ancestor and its descendant cone;
- execute via surviving optimized forms / transparent fallback;
- restore the cone;
- replay.

Record exact consequences and execution costs.

## Frozen gates

CWF1. Zero wrong protected consequences across all episodes and probes.

CWF2. Every capability consequence is externally verified before first use.

CWF3. Every optimized form is independently verified equal to the capability consequence before installation.

CWF4. No optimization changes recorded parent edges or verifier digest.

CWF5. At least 500 non-founder children are admitted.

CWF6. Maximum ancestry depth >= 32.

CWF7. Maximum ancestry depth >= 64.

CWF8. At least 100 disjoint-lineage recombinant children are admitted.

CWF9. At least 50 recombinant children later become parents.

CWF10. At least one recombinant child reaches ancestry depth >= 16.

CWF11. NO_REENTRY maximum ancestry depth <= 2.

CWF12. Full optimized execution cost over episodes 2,001–14,000 < 50% of GENEALOGY_EXECUTION.

CWF13. Full optimized execution cost < 60% of NO_FORM_OPT.

CWF14. Full optimized execution cost < 70% of NO_REENTRY.

CWF15. Full optimized execution cost < 35% of COLD.

CWF16. Median optimized Form cost of capabilities at depth >=32 is <= median optimized Form cost of capabilities at depths 2–4.

CWF17. At least 25 capabilities at ancestry depth >=16 have optimized form cost less than 25% of their inherited genealogical construction cost.

CWF18. All reached remove/restore probes raise execution cost on removal.

CWF19. All reached remove/restore probes restore exact original cost and consequence.

CWF20. Revocation target descendant cone size >=100.

CWF21. Revocation removes 100% of target descendants before next execution.

CWF22. Revocation preserves >=99% of capabilities outside target cone.

CWF23. NO_ANCESTRY either retains an invalid descendant or must conservatively remove strictly more unrelated capabilities.

CWF24. A new post-revocation lineage reaches depth >=16.

CWF25. Post-revocation capability hit rate returns to >=90% of pre-revocation hit rate within 2,000 episodes.

CWF26. Held-out capability hit rate >=90%.

CWF27. Held-out optimized execution cost <40% of COLD.

CWF28. RANDOM_MATE produces strictly fewer disjoint-lineage recombinant children than full system.

CWF29. Archive contains no duplicate exact protected consequences.

CWF30. Deterministic replay reproduces consequence, ancestry, form, revocation, cost, and final-archive hashes.

## Verdicts

- PASS_CONSEQUENCE_WHAKAPAPA_FORM_V1
- PARTIAL_CONSEQUENCE_WHAKAPAPA_FORM_V1
- VALID_NEGATIVE_CONSEQUENCE_WHAKAPAPA_FORM_V1

PASS requires CWF1-CWF30.

## Claim boundary

A PASS would establish only in this exact finite Boolean ecology that:

- semantic consequence, causal provenance, and executable representation can be maintained as separate system objects;
- deep verified ancestry need not imply deep execution;
- optimized form can change while consequence and warrant lineage remain invariant;
- explicit ancestry enables selective revocation;
- cross-lineage verified recombination can be induced without selecting semantic identities;
- the resulting architecture can retain deep developmental history while executing shallow current forms.

It would not establish unbounded development, biological equivalence, general intelligence, or real-CPU speedup.

The target architecture is:

[
oxed{
	extbf{Consequence persists. Whakapapa warrants. Form transforms.}
}
]
