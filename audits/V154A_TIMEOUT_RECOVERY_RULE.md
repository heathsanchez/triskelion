# V154A Timeout Recovery Rule — Frozen Before Manifest Outcome

If eligible V154A run `31946832474` fails solely because the 360-minute GitHub Actions job limit is reached before all 34 predetermined cases are classified, do **not** reduce the corpus, alter eligibility, skip slow cases, substitute cases, or interpret the observed prefix.

The only licensed recovery is an apparatus-only deterministic sharding of the exact same frozen 34-case audit:

1. preserve the existing first-two-per-project SHA256 selection exactly;
2. assign the already selected cases to deterministic shards by their position in the complete frozen ordered 34-case list (e.g. index modulo a fixed shard count frozen before the recovery run);
3. run the unchanged checkout/runtime/baseline/strict-site classifier independently on every case;
4. merge only after every one of the same 34 cases has a terminal classification;
5. apply the unchanged V154A viability gate: at least 12 distinct projects with one or more eligible selected cases;
6. treat any missing shard/case as R10/inconclusive.

This contingency is apparatus-only. It does not license any change to corpus, semantic task, source filter, runtime support, minimum strict-site threshold, or claim boundary.
