# CP3 acquisition pipeline representation correction

Status: **ACQUISITION-ONLY ENGINEERING; PROTECTED SEMANTICS UNOPENED**

## What run 31881785911 established

The run reached the frozen model and consumed two calls on each acquisition case, but it is not used as the final acquisition freeze because the acquisition context extractor supplied the wrong representation of the buggy repository:

- `httpie/5`: selected `env/lib/python3.7/site-packages/_pytest/...` files created by the native verifier environment instead of the project implementation implicated by the failure.
- `youtube-dl/32`: selected unrelated `devscripts/...` files because the fallback traversal took the lexicographically earliest Python files after failing to locate a useful repository frame.

The model responses explicitly identified the missing relevant implementation context. No protected source, protected outcome, fixed implementation, reference patch, or developer solution was used to diagnose this pipeline error.

## Correction

`cp3/source_context_ranker.py` replaces the acquisition-only context selection with a generic, case-independent representation rule:

1. exclude generated/runtime/tooling trees such as `env`, `.venv`, `site-packages`, `.git`, build trees and `devscripts`;
2. prioritize project-local traceback frames from the failing native test;
3. extract identifier tokens from the native failure text;
4. rank remaining project source files by overlap with those identifiers, with additional weight for matching function/class definitions;
5. show focused source excerpts around the matched identifiers within the same frozen context budget.

The ranker never opens BugsInPy `bug_patch.txt`, a fixed revision, or any protected material.

## Scientific treatment

Run 31881785911 is retained as acquisition-pipeline debugging evidence, not as the final acquisition episode. Acquisition cases are the development/training side of the frozen partition and may be used to repair the acquisition representation before capability freeze. The protected partition remains quarantined.

The next acquisition run is the first candidate final freeze under the corrected representation. Within that candidate run the frozen model budget remains two calls per acquisition case plus one synthesis call. No protected evaluation may begin unless both acquisition cases yield native-verified repairs and the resulting capability/RAW-memory artifacts are hash-frozen.
