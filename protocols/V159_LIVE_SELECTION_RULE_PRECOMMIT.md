# V159 Live Selection Rule — PRECOMMIT

This rule is frozen before the zero-model downstream scope census emits an outcome.

## Candidate ancestor

The only candidate ancestor is the already-frozen acquisition artifact:

`cp3_frozen/acquisition/CAPABILITY.json`

It was acquired from the two frozen acquisition cases `httpie/5` and `youtube-dl/32`. Its prior status as a verified acquisition artifact does **not** by itself admit it as a causal developmental ancestor for V159.

## Frozen natural downstream order

1. `thefuck/32`
2. `keras/32`
3. `spacy/2`
4. `fastapi/5`
5. `black/18`
6. `pandas/66`

No order change, post-hoc exclusion, or replacement is allowed after scope-census outcomes.

## Eligibility

A case is eligible only if all are true before any model call on that case:

- buggy revision reproduces a native verifier failure under its exact frozen historical Python image;
- context construction succeeds under the frozen context resolver;
- the candidate capability's already-frozen executable scope matches that buggy-source context;
- no protected solution/fixed implementation is read.

## Prospective role assignment

Take the first two eligible cases in the frozen order.

- first eligible case = `ANCESTOR_QUALIFICATION_CASE`;
- second eligible case = `DOWNSTREAM_DEVELOPMENT_CASE`.

If fewer than two cases are eligible, verdict is `OBSTRUCTED_V159_INSUFFICIENT_NATURAL_SCOPE_FRONTIER` and no live developmental inference is licensed.

## Ancestor qualification gate

The candidate capability is not admitted into `A_t` until the qualification case establishes, under matched seeds/model/calls/verifier:

1. candidate semantic capability beats ancestor-minus/cold on verifier-grounded reachability or frozen efficiency criterion;
2. a fully opaque, same-length, same-serialization-shape capability envelope does not reproduce the advantage;
3. at least one candidate-capability arm produces a native-verifier accepted solution;
4. all compared cells have valid apparatus and source-state synchronization.

If this gate fails, the candidate remains unadmitted and the run terminates `NEGATIVE_V159_ANCESTOR_NOT_CAUSALLY_QUALIFIED` (or `OBSTRUCTED` for apparatus failure). Do not proceed to the downstream development case.

## Admission and restart

On qualification pass only:

- create a fresh unified developmental state;
- set exact verifier config as a verified event;
- set the frozen discovery policy as a verified event;
- install the candidate capability with the qualification evidence attached;
- serialize the event stream;
- terminate the in-memory state;
- reload from event stream;
- require exact state-hash equality and identical scope activation on a frozen replay probe.

This post-qualification state is the prospectively fixed causal ancestor state `A*`.

## Downstream developmental gate

On the second eligible case compare at minimum:

- `DEV`: reloaded `A*`, capability available only if its executable scope matches;
- `DEV_ANCESTOR_MINUS`: same verifier/policy state but candidate ancestor removed before the case;
- `RAW`: frozen acquisition raw memory;
- `RAG`: deterministic retrieval over the same frozen acquisition raw memory;
- `OPAQUE_DEV`: same serialized capability envelope length/shape with semantic labels and values deterministically destroyed;
- `COLD`: no cross-episode retained information.

`ADAPT` is recorded `NOT_AVAILABLE` unless a genuinely matched adaptation mechanism is frozen before any live outcome. No substitute arm may be invented after results.

A natural developmental PASS requires the frozen V159 main protocol plus:

- downstream verified result/reachable frontier present in DEV;
- absent or strictly worse in DEV_ANCESTOR_MINUS under matched budget;
- opaque control does not reproduce the causal advantage;
- raw/RAG do not receive extra model or verifier budget;
- restart gate passed before downstream inference.

Task success without the ancestor-minus frontier separation is not developmental compounding.
