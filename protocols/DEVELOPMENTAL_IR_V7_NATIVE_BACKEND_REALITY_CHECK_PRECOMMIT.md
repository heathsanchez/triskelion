# DEVELOPMENTAL IR V7 — NATIVE BACKEND REALITY CHECK — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

[
oxed{	extbf{Do learned verified macros still buy anything when compiled by a real optimizing native backend, rather than being assigned unit abstract cost?}}
]

V6 established bounded blind grammar expansion under a 24-instruction budget. That result used an abstract instruction-cost model. V7 tests the missing engineering boundary honestly.

## Basis

Use the **final 24-macro language produced by the authoritative V6 result**. Reconstruct each macro from its exact ((arity,truth table)) and D+GROUND expression. No macro identity may be replaced post hoc.

Generate one deterministic workload of 20,000 macro invocations. Each invocation selects:

- one of the 24 final V6 macros by its frozen V6 transfer-reuse weight;
- argument registers from eight live 64-bit registers;
- a destination register.

The same invocation stream is used by every backend.

All arithmetic is unsigned 64-bit bitwise Boolean execution.

## Four native backends

### EXPANDED
Every call site contains the macro's D+GROUND expression expanded directly in C.

### INLINE
Each macro is defined once as a `static inline` C function and invoked at the same call sites.

### OUTLINE
Each macro is defined once as a `__attribute__((noinline))` C function and invoked by call.

### HYBRID
The six highest-reuse V6 macros are `static inline`; the remaining eighteen are `noinline`.

This uses the learned utility signal as a native code-generation policy.

## Compilation

Use the GitHub-hosted Ubuntu runner's system GCC with:

`gcc -O3 -std=c11`

No architecture-specific `-march=native` is permitted.

Record:

- generated C source bytes;
- GCC wall compile time;
- final executable bytes;
- ELF text-section bytes.

## Execution

Each binary:

- initializes the same eight registers from frozen 64-bit constants;
- executes the 20,000-invocation stream repeatedly for 1,000 outer iterations;
- emits a final checksum;
- reports elapsed monotonic-clock nanoseconds.

Run each executable 7 times.

Use the median elapsed time as the primary runtime measurement.

The checksum must be identical across all four variants.

## Frozen gates

N1. All 24 V6 macros are reconstructed and independently reverified before code generation.

N2. All four binaries compile successfully.

N3. All four binaries emit identical checksums on all seven runs.

N4. INLINE median runtime is no worse than 115% of EXPANDED median runtime.

N5. OUTLINE text-section size is less than 60% of EXPANDED text-section size.

N6. HYBRID text-section size is less than 75% of EXPANDED text-section size.

N7. HYBRID median runtime is no worse than 125% of the fastest of EXPANDED/INLINE.

N8. INLINE generated source is less than 35% of EXPANDED generated source size.

N9. OUTLINE generated source is less than 35% of EXPANDED generated source size.

N10. HYBRID generated source is less than 35% of EXPANDED generated source size.

N11. At least one non-expanded backend compiles faster than EXPANDED.

N12. Deterministic regeneration yields identical invocation-stream hash and generated-source hashes.

## Verdicts

- PASS_DEVELOPMENTAL_IR_V7_NATIVE_BACKEND_REALITY_CHECK
- PARTIAL_DEVELOPMENTAL_IR_V7_NATIVE_BACKEND_REALITY_CHECK
- VALID_NEGATIVE_DEVELOPMENTAL_IR_V7_NATIVE_BACKEND_REALITY_CHECK

PASS requires N1-N12.

## Claim boundary

A PASS would show that the learned language can survive contact with a real optimizing compiler as a useful code-generation abstraction, with code-size / source-size / compile-time benefits and bounded runtime overhead.

A PARTIAL or NEGATIVE result is equally informative. In particular, it may show that the earlier abstract `CAP=1` execution model does **not** automatically translate into CPU speed. That would constrain the language design toward compilation/search amortization, profile-guided inlining, caching, or hardware-aware backends rather than unsupported runtime-speed claims.
