from __future__ import annotations

import acquire_bugsinpy_capability as acquisition
import bugsinpy_four_arm_v2 as env_adapter

acquisition.native_test = env_adapter.native_test

if __name__ == "__main__":
    acquisition.main()
