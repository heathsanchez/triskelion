# E0002 — Preflight lexical separator

## Observation
E0001 used only ordinary Triton launches plus tensor allocation, yet the remote service returned the exact same pre-execution policy error as the PyTorch baseline. This weakens the hypothesis that `torch.linalg.eigh` itself is the trigger.

## Live rival explanations
H1 — source-level preflight is conservatively matching source text associated with forbidden asynchronous execution; E0001's diagnostic comments themselves contained the relevant terminology.

H2 — some actual operation in the implementation is prohibited, independent of comments/source wording.

## Smallest separator
Keep the E0001 computation unchanged while removing all comments and identifiers referring to the prohibited execution concept from the submitted file. Do not alter the experiment ledger.

## Prediction
If the submission reaches compilation or correctness evaluation, the prior error was source/preflight lexical rather than a property of executed Triton work. If the identical policy error remains, reject H1 and inspect another preflight dimension.

## Kill criterion
This remains infrastructure diagnosis only. No task-capability or speed claim is licensed.
