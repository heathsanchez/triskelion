# V145A — Precompiled-checkout apparatus addendum

Frozen before the first V145 T2/T3 model outcome.

V145's scientific assumptions, tasks, seeds, arms, budgets and semantic gates are unchanged. This addendum changes only repeated environment provisioning cost.

For each frozen task, the controller creates one disposable BugsInPy buggy checkout and runs the full pinned exact-runtime `bugsinpy-compile` + `bugsinpy-test` baseline once. That prepared checkout is then the immutable template for all compared arms on that task.

For each candidate attempt the template is copied to a fresh disposable directory before the model patch is applied.

If the candidate diff changes only ordinary `.py` source files and does not touch a path containing `test`/`tests`, `setup.py`, `setup.cfg`, `pyproject.toml`, requirements files, C/C++/Cython sources, or build metadata, semantic verification runs the same pinned exact-runtime `bugsinpy-test` command directly in the already-compiled copy. Python source is interpreted at test time; no compiled candidate artifact is being reused.

If a candidate touches any build-sensitive/non-Python file, the runner falls back to the original full exact-runtime `native_test` (`bugsinpy-compile` then `bugsinpy-test`).

Controls:

1. Every arm for a task starts from a copy of the same prepared checkout.
2. The template itself is never patched.
3. Test-file edits remain rejected by the model prompt and are never accepted as scientific success.
4. Candidate verification still uses the BugsInPy native test command inside the same pinned historical Python image.
5. A missing/corrupt template, Docker failure, copy failure, or test environment failure is R10.
6. This optimization cannot turn a failing native test into a pass by classification rule; only the native test exit/failure files determine semantic success.

No capability or development claim is altered by this addendum.