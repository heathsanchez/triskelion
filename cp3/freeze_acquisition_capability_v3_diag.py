#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import freeze_acquisition_capability as v1
import freeze_acquisition_capability_v2 as v2

# Diagnostic-only wrapper. It does not alter the prompt, model, seed,
# temperature, token budget, acquisition evidence, parser semantics, or
# capability validator. It only persists the first parsed JSON object before
# validation so schema failures can be diagnosed without opening protected data.
_original_parse = v1.parse_json_object


def _parse_and_record(text: str) -> dict:
    obj = v2.parse_json_object_first_complete(text)
    out = Path(sys.argv[1]) if len(sys.argv) == 2 else Path("cp3_freeze/acquisition")
    out.mkdir(parents=True, exist_ok=True)
    (out / "PREVALIDATION_PARSED_RESPONSE.json").write_text(
        json.dumps(obj, indent=2, sort_keys=True) + "\n"
    )
    return obj


v1.parse_json_object = _parse_and_record
v1.main()
