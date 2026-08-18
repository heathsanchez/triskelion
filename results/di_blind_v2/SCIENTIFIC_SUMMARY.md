# DI Blind V2 — scientific result

**Verdict: `VALID_NEGATIVE_V2_NO_CONSTRUCTION`**

V2 was a clean blind negative. The frozen checker incorrectly **accepted** the naturally selected malformed case `bad/tutorial/071_BogusRecursor.ndjson` (expected `reject`). The corpus commitment reproduced after the candidate batch was sealed.

The V2 line-range interface improved the V1 apparatus but did not yield a capability: 3/16 generations were admissible under the frozen schema; all three admissible patches failed to build, so no candidate was retained. Therefore protected transfer and causal ablation were not reached. Base-weight updates were 0.

This means the preregistered O1→O2 developmental dependency gate is **inapplicable for V2**: V2 did not acquire autonomous O1. No O2 experiment may be run from this V2 lineage.

The public `result.json` preserves all verdict-relevant fields and hashes verbose compiler-error tails. The complete original `result.json` is anchored by `full_private_result_sha256` and the GitHub Actions artifact digest recorded there.
