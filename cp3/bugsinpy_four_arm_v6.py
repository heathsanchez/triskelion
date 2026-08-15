from __future__ import annotations

import bugsinpy_four_arm as base
import bugsinpy_four_arm_v4 as env_adapter
import source_context_ranker_v2 as context_adapter
import structured_edit_protocol as edits

# Identical infrastructure for every future protected arm.
base.native_test = env_adapter.native_test
base.collect_context = context_adapter.collect_context
base.visible_request = edits.visible_request
base.extract_diff = edits.extract_edits
base.apply_diff = edits.apply_edits

if __name__ == "__main__":
    base.main()
