# Potential upstream nanoda repair

This note is intentionally not an upstream submission.

At `ammkrn/nanoda_lib@418320295890faed83a96fd97907b12a3b6728c2` (also upstream `master` on 2026-08-14), `src/parser.rs` assumes exported internalization-table back-reference IDs are continuous and identical to internal hash-cons DAG indices.

The tested repair introduces explicit external-ID -> internal-pointer maps for Names, Levels, and Exprs and routes all parser lookups/bindings through those maps.

Evidence in this branch:

- exact Arena causal case + held-out transfer + ablation
- all static Arena NDJSON cases: 8/8 after repair, no regressions
- 256 randomized valid arbitrary-ID encodings accepted after repair vs 0/256 before
- 512 malformed controls rejected after repair
- all seven later duplicate/misnamed tutorial cases move from decline to Arena-normalized reject without another primitive
- full downloadable Arena suite: 152/161 -> 161/161, 9 declines -> 0, no false accepts, no regressions

Before proposing upstream, the patch should be cleaned into idiomatic Rust, dead `assert_in/assert_il/assert_ie` methods removed, focused parser unit tests added, and the upstream maintainer's preferred error behavior (panic/reject/decline) confirmed.
