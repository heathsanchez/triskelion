# V161 — Local Instantiation Binding Separator

Status: FROZEN BEFORE V161 OUTCOMES
Date: 2026-08-17
Parent evidence: V159 negative, V160 `OBSTRUCTED_V160_ROUTING_REPAIRED_NO_SEMANTIC_SOLUTION`.

## Question

After V160 causally repaired routing to `thefuck/rules/ls_lah.py`, why did the semantic capability still fail to solve the natural task?

V160 showed a repeated local failure mode across all three seeds:

1. the semantic capability without routing acted at the wrong source locus;
2. semantic capability + right locus produced executable edits at the right locus on 3/3 seeds;
3. those edits retained substring-style matching and successively patched individual negatives (`-lah`, then `pacman`), after which the verifier exposed `lsof` as another false positive;
4. no arm produced a native-verified solution.

The live residual is therefore local *instantiation*: whether the retained abstract capability can be bound to the local predicate structure exposed by verifier observations.

## Frozen task / apparatus

- task: BugsInPy `thefuck/32`
- BugsInPy HEAD: `11c5f1eea954a42132cfd06bf257766a7963e0fd`
- model: `Qwen/Qwen3.5-9B`
- seeds: `202608171, 202608172, 202608173`
- max model calls: 2
- max output tokens per call: 2048
- exact historical native verifier and structured-edit trust boundary inherited unchanged from V159/V160
- persistent workspace and post-failure source synchronization unchanged
- right locus fixed to `thefuck/rules/ls_lah.py`
- no protected fixed patch may be inspected or injected

## Instantiation packets

The RIGHT packet is derived only from verifier-observed examples already emitted in V160. It does not provide replacement code. It states the local binding relation that distinguishes the observed positive/negative examples:

- positive commands begin with the standalone command token `ls` (`ls`, `ls file.py`, `ls /opt`)
- negative observations include `ls -lah /opt`, `pacman -S binutils`, and `lsof`
- bind the retained repair law to command-token structure rather than arbitrary substring occurrence

The WRONG packet has the same serialized template and is length-matched, but binds the law to a deliberately incorrect relation: arbitrary substring occurrence is treated as the intended local discriminator. It must not mention a protected solution.

## Arms

1. `SEM_LOCUS_NONE` — semantic capability + correct locus; no instantiation packet.
2. `SEM_LOCUS_RIGHT_BIND` — same semantic capability + same correct locus + RIGHT instantiation packet.
3. `SEM_LOCUS_WRONG_BIND` — same semantic capability + same correct locus + WRONG instantiation packet.
4. `OPAQUE_LOCUS_RIGHT_BIND` — opaque length-matched capability + same correct locus + RIGHT packet.
5. `COLD_LOCUS_RIGHT_BIND` — no capability + same correct locus + RIGHT packet.

The semantic capability bytes are identical across arms 1–3. The locus signal is identical across all five arms. RIGHT and WRONG packets must have identical character length.

## Primary endpoint

Native verifier-confirmed solution of `thefuck/32`.

A V161 semantic-instantiation pass requires:

- `SEM_LOCUS_RIGHT_BIND` solves >=1/3 seeds; and
- solves more seeds than both `SEM_LOCUS_NONE` and `SEM_LOCUS_WRONG_BIND`; and
- solves more seeds than both `OPAQUE_LOCUS_RIGHT_BIND` and `COLD_LOCUS_RIGHT_BIND`.

This is the only result licensed as evidence that capability semantics + routing + correct local binding jointly produce verified transfer.

## Secondary mechanism endpoint

Record, per arm/seed, whether the first executable edit replaces substring-style matching with a token/command-bound discriminator. This mechanism endpoint cannot upgrade a 0-solve result to PASS.

## Interpretation

- RIGHT semantic arm uniquely solves -> `PASS_V161_LOCAL_INSTANTIATION_CAUSALLY_COMPLETES_TRANSFER`.
- RIGHT packet also solves in cold/opaque -> local binding is sufficient; retained capability semantics not needed.
- RIGHT packet changes mechanism but no arm solves -> `OBSTRUCTED_V161_BINDING_REPAIRED_NO_VERIFIED_SOLUTION`.
- RIGHT and WRONG behave similarly -> `NEGATIVE_V161_LOCAL_BINDING_NOT_CAUSAL`.
- R10 / source-sync / apparatus failure -> OBSTRUCTED only.

## Claim boundary

V161 tests one natural task and one previously acquired capability under a fixed model/budget. A pass would not establish general developmental learning. A negative does not erase earlier bounded developmental results. V159 and V160 remain immutable evidence regardless of V161 outcome.
