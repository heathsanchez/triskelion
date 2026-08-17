import importlib
import sys
from pathlib import Path


def test_v159_safe_runner_has_no_precompiled_template_side_effects():
    cp3 = str(Path("cp3").resolve())
    if cp3 not in sys.path:
        sys.path.insert(0, cp3)

    base = importlib.import_module("bugsinpy_four_arm")
    exact = importlib.import_module("bugsinpy_exact_runtime")
    original_checkout = base.checkout_buggy
    original_native = exact.native_test

    runner = importlib.import_module("v159_safe_persistent_runner")

    assert "v145_precompiled_runner" not in sys.modules
    assert base.checkout_buggy is original_checkout
    assert exact.native_test is original_native
    assert runner.base.checkout_buggy.__name__ == "checkout_buggy"
    assert runner.exact_runtime.native_test.__name__ == "native_test"
