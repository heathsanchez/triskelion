#!/usr/bin/env python3
from __future__ import annotations

import v151_capability_compilation_loss_separator as experiment

# Exact V149 frozen capability object recovered from the immutable V149 result
# artifact before any V151 model outcome. This wrapper changes no V151 arm,
# budget, task, context, verifier, output protocol, or classification rule.
experiment.O1 = {
    "ancestor_ids": [],
    "applicability_test": "Run the test suite for the item parsing module. If the test case involving an escaped separator (e.g., input containing a backslash followed by a separator character) fails with an assertion error indicating incorrect key-value splitting, this policy is applicable.",
    "artifact_sha256": "7ebb7fb26da6d137c13c1a08bafd7e540dbd52f25e04cf4298502e5ce5428546",
    "capability_id": "V145.O1",
    "generation": "O1",
    "instruction": "When parsing key-value pairs with custom separators, first identify all escape sequences (a backslash followed by a separator) and record their byte spans. Then, iterate through separator matches; only treat a separator as a delimiter if it does not fall entirely within the span of any identified escape sequence.",
    "postconditions": [
        "The parser correctly identifies the position of all escape sequences before processing separators.",
        "Separators located within the span of an escape sequence are ignored as delimiters.",
        "The resulting key-value pairs accurately reflect the intended structure, with escaped separators preserved as part of the key or value.",
        "Tests for escaped separators pass successfully."
    ],
    "preconditions": [
        "The system is parsing key-value pairs using a parser that accepts custom separators.",
        "The input string may contain escaped separators (represented as a backslash followed by the separator character).",
        "The current implementation fails to correctly distinguish between escaped separators and actual delimiters, causing incorrect key-value splitting."
    ],
    "source_intervention_sha256": "b7f419e7993e92164969b7a99689f01dfa279ce2d1615e25fce0bb21486f472d"
}

if __name__ == "__main__":
    experiment.main()
