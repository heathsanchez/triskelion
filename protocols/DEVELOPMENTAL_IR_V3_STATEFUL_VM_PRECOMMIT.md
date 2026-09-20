# DEVELOPMENTAL IR V3 — STATEFUL VM — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

[
oxed{	extbf{Can the one-anchor directed-difference developmental IR grow beyond an ALU into exact state, memory, data-dependent control flow, bounded loops, and reusable verified programs?}}
]

V1 showed a verified developmental Boolean IR. V2 showed an emergent exact 8-bit ALU ISA with strong persistent-capability, recombination, semantic-quotient, ablation, and deterministic-replay signals. V3 tests the next boundary: **stateful programs**.

This is not a claim of Turing universality. Loops are bounded by a frozen symbolic step horizon.

## Kernel

The trusted developmental kernel remains unchanged:

- GROUND = 1
- INPUT
- (D(a,b)=
eg aland b)
- VERIFY
- PROMOTE

No branch, register, RAM, loop, arithmetic operation, or VM instruction is a kernel primitive.

All Boolean and 8-bit operations used by the VM are compiled to the D+GROUND substrate inherited from V2.

## Exact universe

Two independent 8-bit input words (A,B).

All

[
2^{16}=65,536
]

input pairs are represented simultaneously as exact truth vectors.

A program therefore executes symbolically over every input pair at once.

## Stateful VM

State contains:

- three 8-bit registers: R0, R1, R2
- two 8-bit RAM cells: M0, M1
- one-hot program counter over 8 instruction slots
- halted bit

Initial state:

- R0 = input word A or an inherited verified task output
- R1 = input word B or an inherited verified task output
- R2 = 0
- M0 = M1 = 0
- PC = 0
- HALTED = false

## Source VM instruction set

The source VM may use:

- MOV dst, src
- XOR dst, src
- ADD dst, src
- INC dst
- DEC dst
- ANDI dst, imm8
- LOAD dst, M0/M1
- STORE M0/M1, src
- JZ reg, target
- JMP target
- HALT

These are source conveniences only. Their semantics must compile to D+GROUND-derived Boolean / word circuits.

### Data-dependent control flow

JZ is implemented symbolically:

[
m_{mathrm{true}} = PC_i land (reg=0)
]

[
m_{mathrm{false}} = PC_i land 
eg(reg=0)
]

and the next state is selected with derived Boolean multiplexers.

Host-language branching on a particular input row is forbidden in the symbolic IR executor.

## Bounded loop horizon

Every program is symbolically unrolled for exactly 24 VM steps.

Frozen program templates are constructed so every input lane should halt within 24 steps.

The external exact authority separately evaluates the VM semantics over the full 65,536-input carrier and verifies:

- all lanes halted by step 24;
- protected output R0 is exactly equal to the symbolic D-IR output.

Any non-halting lane is a verification failure.

## Frozen template families

At least these families must be represented:

1. BRANCH — data-dependent JZ chooses between two arithmetic paths.
2. MEMORY — STORE/LOAD round-trip affects a later arithmetic result.
3. COUNTDOWN — counter masked by ANDI <= 7, DEC/JZ/JMP loop.
4. MEMORY_LOOP — bounded loop repeatedly updates a RAM cell then reloads it.
5. BRANCH_MEMORY — branch chooses which value is written/read.
6. MIXED — memory + arithmetic + conditional control.

Program variants may deterministically permute registers, RAM cell choice, immediate masks, and arithmetic instruction.

No post-outcome template rescue is allowed.

## Developmental workload

Run 1,500 exact stateful-program tasks.

### Phase 1 — curriculum, tasks 1–200
Programs operate directly on A,B and span all template families.

### Phase 2 — descendants, tasks 201–900
Each program receives at least one previously verified task output as an initial register value. TREE/LOCAL_DAG receive its fully expanded historical program circuit. DEVELOPMENTAL may invoke the promoted output-bit capabilities.

### Phase 3 — stateful semantic twins, tasks 901–1,100
Syntax-distinct stateful programs must preserve the protected R0 consequence using frozen identities such as:

- STORE then LOAD the same value;
- MOV through a temporary register;
- branch with consequence-equivalent arms;
- zero-iteration masked loop;
- double XOR with the same verified zero word.

The programs must genuinely exercise state/control constructs even though protected output is equivalent.

### Phase 4 — recombinant programs, tasks 1,101–1,300
Choose outputs from two distinct ancestry regions, use them as R0/R1, run a mixed stateful template, verify the child, and allow promotion.

Track later reuse of recombinant children.

### Phase 5 — frozen stateful ISA, tasks 1,301–1,500
Freeze the capability archive. New held-out stateful programs may use existing capabilities but no new capability may be promoted.

## Execution arms

### TREE
Fully expanded D tree of all inherited parent programs and the current stateful symbolic program.

### LOCAL_DAG
Task-local D hash-consing only.

### SYNTAX_ISA
Persistent reuse only when exact D syntax matches.

### DEVELOPMENTAL_ISA
Persistent reuse by exact verified protected bit consequence.

The capability archive contains exact protected R0-bit consequences. A matching verified bit may execute as a unit-cost CAP leaf.

## Costs

- D execution = 1
- CAP invocation = 1
- INPUT/GROUND = 0
- VERIFY = counted separately
- PROMOTE = 1 per newly installed bit capability

Primary learned-ISA comparison is DEVELOPMENTAL versus LOCAL_DAG.

## Causal controls

- COLD_ISA = LOCAL_DAG-equivalent persistent state cleared per task.
- NO_PROMOTION = verify but never install.
- NO_WARRANT = proposals install zero capabilities.
- SYNTAX_ISA = syntax-only persistent reuse.
- NO_RECOMBINATION = recombinant outputs verify but are not promoted.
- ABLATE_TOP16 = remove the 16 most reused pre-Phase-5 capabilities.
- LOW16 = remove 16 low-reuse age-matched capabilities.

## Correctness / statefulness probes

S1. All V2 Boolean and 8-bit operator prerequisites used by the VM remain exact.

S2. Each template family has at least one direct A,B instance exhaustively verified on all 65,536 input pairs.

S3. Every direct template instance halts on every lane within 24 symbolic steps.

S4. Across all 1,500 tasks, symbolic D-IR protected R0 equals independent host-side VM semantics exactly.

S5. MEMORY separator: replacing STORE with a no-op changes at least one protected output in a frozen memory template.

S6. BRANCH separator: replacing JZ with unconditional fallthrough changes at least one protected output in a frozen branch template.

S7. LOOP separator: replacing DEC with no-op causes either a protected mismatch or non-halting lane in a frozen countdown template.

## Efficiency / developmental gates

S8. DEVELOPMENTAL execution cost < 25% of LOCAL_DAG over the full stream.

S9. DEVELOPMENTAL total including VERIFY+PROMOTE < 40% of LOCAL_DAG execution.

S10. State-semantic-twin DEVELOPMENTAL cost < 50% of SYNTAX_ISA cost.

S11. At least 90% of Phase-5 tasks invoke a learned capability.

S12. COLD_ISA execution >= 4x DEVELOPMENTAL execution.

S13. NO_PROMOTION execution >= 4x DEVELOPMENTAL execution.

S14. NO_WARRANT installs zero capabilities.

S15. At least 50 recombinant Phase-4 capabilities are reused by later tasks.

S16. NO_RECOMBINATION Phase-4+5 cost is strictly higher than DEVELOPMENTAL Phase-4+5 cost.

S17. ABLATE_TOP16 raises Phase-5 execution cost by at least 15%.

S18. LOW16 raises Phase-5 cost by less than half the TOP16 increase.

S19. No duplicate protected semantic capabilities exist.

S20. Deterministic replay from empty state yields identical ledger hash and cost vector.

## Additional outputs

Report:

- exact source VM listing for one representative of each template family;
- per-template halt margin;
- per-phase execution costs;
- branch / memory / loop separator evidence;
- capability count;
- semantic and syntax reuse;
- task ancestry depth;
- recombinant child reuse;
- frozen-ISA hit rate;
- top-16 ablation and low-16 control;
- deterministic ledger hash;
- S1–S20.

## Verdicts

- PASS_DEVELOPMENTAL_IR_V3_STATEFUL_VM
- PARTIAL_DEVELOPMENTAL_IR_V3_STATEFUL_VM
- VALID_NEGATIVE_DEVELOPMENTAL_IR_V3_STATEFUL_VM

PASS requires S1–S20.

## Claim boundary

A PASS would establish only that, on an exact finite two-word 8-bit input universe and a 24-step bounded symbolic VM:

- D+GROUND can host exact registers, RAM, data-dependent branch, and bounded loops;
- verified stateful program consequences can become a reusable learned ISA;
- learned capabilities can reduce exact execution cost beyond task-local DAG and syntax-only reuse;
- state, branch, loop, and memory constructs are causally non-decorative under frozen separators.

It would **not** establish unbounded loops, Turing universality, lower wall-clock cost than production virtual machines, or unrestricted software synthesis.
