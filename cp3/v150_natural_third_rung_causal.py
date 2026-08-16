from __future__ import annotations

import v145_precompiled_runner  # noqa: F401
import bugsinpy_four_arm as base
import v145_natural_third_rung_causal as experiment
from v150_exact_definition_slice import resolve_exact_slice


def exact_slice_collect_context(work, baseline_output, *, max_files=6, max_chars=36000):
    context, files, _audit = resolve_exact_slice(work, baseline_output)
    return context, files

base.collect_context = exact_slice_collect_context
experiment.base.collect_context = exact_slice_collect_context

if __name__ == '__main__':
    experiment.main()
