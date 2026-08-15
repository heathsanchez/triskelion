#!/usr/bin/env python3
"""Parser-only recovery wrapper for TRISKELION_CP3_ACQUISITION_FREEZE_V1.

Scientific inputs, prompt, model, seed, temperature, token budget, validation,
and capability schema are unchanged from freeze_acquisition_capability.py.
V1 reached the frozen model successfully but failed to parse because the model
returned valid JSON followed by trailing text. This wrapper changes only JSON
framing: decode the first complete object beginning at the first '{'.
"""
from __future__ import annotations

import json
import sys

import freeze_acquisition_capability as v1


def parse_first_json_object(text: str) -> dict:
    first = text.find("{")
    if first < 0:
        raise ValueError("model did not return a JSON object")
    obj, _end = json.JSONDecoder().raw_decode(text[first:])
    if not isinstance(obj, dict):
        raise ValueError("first decoded JSON value is not an object")
    return obj


v1.parse_json_object = parse_first_json_object

if __name__ == "__main__":
    v1.main()
