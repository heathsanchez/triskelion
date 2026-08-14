#!/usr/bin/env python3
"""NONCLAIM shortened diagnostic for V102. Scientific protocol is unchanged except task/candidate budgets are smaller."""
import importlib.util
from pathlib import Path

BASE = Path(__file__).with_name('METALOGIC_V102_FRESH_SPLIT_EXPRESSION_CONSTRUCTOR.py')
spec = importlib.util.spec_from_file_location('v102', BASE)
v102 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v102)

v102.SEED = 'V102P_EXPRESSION_CONSTRUCTOR_PREFLIGHT_2026-08-14'
v102.TEST_N = 6
v102.CAP_BASE = 100
v102.CAP_EXPR = 120

if __name__ == '__main__':
    v102.main()
