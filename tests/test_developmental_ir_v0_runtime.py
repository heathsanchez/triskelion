from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from developmental_ir.runtime import (
    Capability,
    CapabilityArchive,
    archive_from_v6_result,
    compile_c_expr,
    eval_term,
    expand_term,
)


V6_RESULT = Path("results/developmental_ir_v6_blind_grammar_expansion/result.json")


class DevelopmentalIRV0Tests(unittest.TestCase):
    def test_v6_pack_roundtrip(self):
        archive = archive_from_v6_result(V6_RESULT)
        self.assertEqual(len(archive.ids()), 24)
        original_hash = archive.pack_hash()

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "pack.json"
            archive.save(p)
            loaded = CapabilityArchive.load(p)
            self.assertEqual(loaded.pack_hash(), original_hash)
            self.assertEqual(loaded.ids(), archive.ids())

    def test_all_v6_capabilities_reverify(self):
        archive = archive_from_v6_result(V6_RESULT)
        self.assertTrue(all(archive.get(i).reverify() for i in archive.ids()))

    def test_tamper_rejected(self):
        cap = Capability.verified("not", 1, 1, "D(x0,1)")
        row = cap.to_json()
        row["table"] ^= 1
        with self.assertRaises(ValueError):
            Capability.from_json(row)

    def test_transparent_capability_erasure_preserves_semantics(self):
        archive = archive_from_v6_result(V6_RESULT)
        cap_id = archive.ids()[0]
        cap = archive.get(cap_id)
        args = [{"op": "arg", "index": i} for i in range(cap.arity)]
        term = {"op": "cap", "id": cap_id, "args": args}
        expanded = expand_term(term, archive)

        # Use the complete arity truth-table carrier as bitset inputs.
        rows = 1 << cap.arity
        mask = (1 << rows) - 1
        actual = []
        for i in range(cap.arity):
            v = 0
            for row in range(rows):
                if (row >> i) & 1:
                    v |= 1 << row
            actual.append(v)

        got_cap = eval_term(term, tuple(actual), mask, archive)
        got_expanded = eval_term(expanded, tuple(actual), mask, archive)
        self.assertEqual(got_cap, cap.table)
        self.assertEqual(got_expanded, cap.table)

    def test_default_c_backend_is_transparent(self):
        archive = archive_from_v6_result(V6_RESULT)
        cap_id = archive.ids()[0]
        cap = archive.get(cap_id)
        term = {
            "op": "cap",
            "id": cap_id,
            "args": [{"op": "arg", "index": i} for i in range(cap.arity)],
        }
        c = compile_c_expr(term, archive, [f"x{i}" for i in range(cap.arity)])
        self.assertNotIn("cap_", c)
        self.assertIn("~", c)

    def test_archive_rejects_unverified_capability(self):
        cap = Capability.verified("id", 1, 2, "x0")
        bad = Capability(
            id=cap.id,
            arity=cap.arity,
            table=cap.table ^ 1,
            expansion=cap.expansion,
            digest=cap.digest,
            metadata={},
        )
        archive = CapabilityArchive()
        with self.assertRaises(ValueError):
            archive.add(bad)


if __name__ == "__main__":
    unittest.main()
