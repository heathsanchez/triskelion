#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import freeze_acquisition_capability as v1
import freeze_acquisition_capability_v2 as v2

# Diagnostic-only wrapper. Scientific inputs are unchanged. This records the
# first complete JSON object before the frozen validator runs.

def _parse_and_record(text: str) -> dict:
    obj = v2.parse_first_json_object(text)
    out = Path(sys.argv[1]) if len(sys.argv) == 2 else Path("cp3_freeze/acquisition")
    out.mkdir(parents=True, exist_ok=True)
    (out / "PREVALIDATION_PARSED_RESPONSE.json").write_text(
        json.dumps(obj, indent=2, sort_keys=True) + "\n"
    )
    (out / "MODEL_RESPONSE_RAW.txt").write_text(text)
    return obj


v1.parse_json_object = _parse_and_record
v1.main()
