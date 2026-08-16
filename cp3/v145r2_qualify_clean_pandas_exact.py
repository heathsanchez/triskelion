#!/usr/bin/env python3
from pathlib import Path

import v145r1_qualify_clean_pandas_exact as r1

# V145R2 is an exposure-only revision. Reuse the exact R1 qualification engine
# while changing only the protocol identity and prefrozen denylist path.
r1.PROTOCOL = "V145R2_CLEAN_THIRD_RUNG_ELIGIBILITY"
r1.DENYLIST_PATH = Path("protocols/V145R2_EXPOSURE_DENYLIST.json")

if __name__ == "__main__":
    r1.main()
