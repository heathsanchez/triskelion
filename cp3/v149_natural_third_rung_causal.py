from __future__ import annotations

# Install the unchanged V145A exact-runtime/precompiled apparatus.
import v145_precompiled_runner  # noqa: F401
import bugsinpy_four_arm as base
import v145_natural_third_rung_causal as experiment
from v149_context_resolver import resolve_context


def resolved_collect_context(work, baseline_output, *, max_files=6, max_chars=36000):
    context, files, _audit = resolve_context(work, baseline_output, max_files=max_files, max_chars=max_chars)
    return context, files

# Only the visible-source adapter changes from V145. The experiment module
# references the same base module object, so this patch applies to preparation
# and every matched arm without touching tasks/seeds/budgets/capability logic.
base.collect_context = resolved_collect_context
experiment.base.collect_context = resolved_collect_context

if __name__ == '__main__':
    experiment.main()
