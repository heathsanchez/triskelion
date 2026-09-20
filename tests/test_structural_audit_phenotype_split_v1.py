import unittest

from experiments.structural_audit_phenotype_split_v1 import (
    OP_COUNT,
    encode_op,
    canonical_key,
    independent_metrics,
    v4_descriptor,
    reconstruct_v4_canonical_orbits,
    orbit_symmetry_diagnostic,
    family_analysis,
    stable_hash,
    FAMILY_FIELDS,
)


class StructuralAuditV1Tests(unittest.TestCase):
    def test_projection_left_metrics(self):
        # Raw d(a,b)=a, ground=0. Do not canonicalize through transpose here.
        key = encode_op([a for a in range(3) for b in range(3)])
        m = independent_metrics(key)
        self.assertEqual((m["d0"], m["d1"], m["d2"], m["d3"]), (3,3,3,3))
        self.assertEqual(m["recombinant3"], 0)
        self.assertEqual(m["recur_distinct_sum"], 15)
        self.assertEqual(m["recur_distinct_max"], 2)
        self.assertEqual(m["recur_cycle_sum"], 15)
        self.assertEqual(m["recur_cycle_max"], 2)

    def test_projection_exposes_transpose_sensitive_recurrence(self):
        key = encode_op([a for a in range(3) for b in range(3)])
        diag = orbit_symmetry_diagnostic(key)
        self.assertEqual(diag["carrier_relabel_differences"], [])
        self.assertIn("recur_cycle_sum", diag["transpose_differences"])
        self.assertIn("recur_cycle_max", diag["transpose_differences"])
        self.assertNotIn("d3", diag["transpose_differences"])
        self.assertNotIn("recombinant3", diag["transpose_differences"])

    def test_v4_reconstructs_projection_orbit_uniquely(self):
        code = encode_op([a for a in range(3) for b in range(3)])
        key = canonical_key(code)
        desc = v4_descriptor(key)
        recovered = reconstruct_v4_canonical_orbits(desc)
        self.assertEqual(recovered["canonical_orbits"], {key})
        self.assertGreaterEqual(recovered["consistent_orientations"], 1)

    def test_family_split_excludes_derived_rank_labels(self):
        expected = {
            "F1_final_semantic_reach": ("binary","no_ground"),
            "F2_bounded_derivational_geometry": ("d0","d1","d2","d3","recombinant3"),
            "F3_recurrence_dynamics": (
                "recur_distinct_sum","recur_distinct_max",
                "recur_cycle_sum","recur_cycle_max",
            ),
            "F4_mutation_neighborhood": (
                "mutation_complete","mutation_generative","mutation_ref_independent",
            ),
        }
        for name, fields in expected.items():
            self.assertEqual(FAMILY_FIELDS[name], fields)
        for fields in FAMILY_FIELDS.values():
            self.assertNotIn("joint_developmental", fields)
            self.assertNotIn("pareto", fields)

    def test_family_analysis_is_input_order_independent(self):
        base = {
            "weight": 1,
            "binary": 1,
            "no_ground": 1,
            "d0": 3,
            "d1": 3,
            "d2": 3,
            "d3": 3,
            "recombinant3": 0,
            "recur_distinct_sum": 9,
            "recur_distinct_max": 1,
            "recur_cycle_sum": 9,
            "recur_cycle_max": 1,
            "mutation_complete": 0,
            "mutation_generative": 0,
            "mutation_ref_independent": 0,
        }
        a = dict(base, key=30)
        b = dict(base, key=82, binary=2, no_ground=2, d3=4)
        forward = family_analysis([a,b])
        reverse = family_analysis([b,a])
        self.assertEqual(stable_hash(forward), stable_hash(reverse))


if __name__ == "__main__":
    unittest.main()
