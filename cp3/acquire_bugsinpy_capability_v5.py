from __future__ import annotations

import acquire_bugsinpy_capability as acquisition
import bugsinpy_four_arm_v4 as env_adapter
import source_context_ranker

acquisition.native_test = env_adapter.native_test
acquisition.collect_context = source_context_ranker.collect_context

if __name__ == "__main__":
    acquisition.main()
