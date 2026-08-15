from __future__ import annotations

import acquire_bugsinpy_capability as acquisition
import bugsinpy_four_arm_v4 as env_adapter
import source_context_ranker_v2 as context_adapter
import structured_edit_protocol as edits
from river_qwen35_provider import Qwen35ChatRiverProvider

acquisition.native_test = env_adapter.native_test
acquisition.collect_context = context_adapter.collect_context
acquisition.visible_request = edits.visible_request
acquisition.extract_diff = edits.extract_edits
acquisition.apply_diff = edits.apply_edits
acquisition.changed_files = edits.changed_files
acquisition.RiverProvider = Qwen35ChatRiverProvider

if __name__ == "__main__":
    acquisition.main()
