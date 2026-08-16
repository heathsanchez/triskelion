"""Apparatus-only recovery for V135 hosted run 31917898039.

The frozen V135 scientific protocol, task enumeration, candidate grammar, gates,
and decision rules are unchanged. The first hosted run crashed when a causal
QuixBugs mutation did not terminate within the verifier timeout. This wrapper
converts subprocess TimeoutExpired into the explicit failing verifier signature
('TIMEOUT', rc=124), matching the handling already used in earlier V108 work.

A 10-second per-candidate ceiling is used because QuixBugs unit tests are tiny;
timeout is treated as an observable failure signature, never as a PASS.
"""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

TARGET = Path(__file__).with_name('V135_DEVELOPMENTAL_QUOTIENT_CAPSTONE.py')
spec = importlib.util.spec_from_file_location('v135_frozen', TARGET)
m = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(m)

_original_verify = m.verify

def timeout_safe_verify(root, program, path, content, timeout=10):
    try:
        return _original_verify(root, program, path, content, timeout=10)
    except subprocess.TimeoutExpired:
        return {'pass': False, 'failures': ('TIMEOUT',), 'returncode': 124}

m.verify = timeout_safe_verify

if __name__ == '__main__':
    m.main()
