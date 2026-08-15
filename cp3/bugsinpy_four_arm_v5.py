from __future__ import annotations

import bugsinpy_four_arm as base
import bugsinpy_four_arm_v4 as env_adapter
import source_context_ranker

# Shared infrastructure for every future protected arm. This wrapper does not
# change arm semantics: it supplies the same historical native verifier and the
# same acquisition-developed source representation to COLD/RAW/ALWAYS/VERIFIED.
base.native_test = env_adapter.native_test
base.collect_context = source_context_ranker.collect_context

if __name__ == "__main__":
    base.main()
