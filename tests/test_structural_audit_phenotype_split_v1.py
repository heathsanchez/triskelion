import unittest

from experiments.structural_audit_phenotype_split_v1 import (
    OP_COUNT,
    encode_op,
    canonical_key,
    independent_metrics,
    v4_descriptor,
    reconstruct_v4_canonical_orbits,
    FAMILY_FIELDS,
)


class StructuralAuditV1Tests(unittest.TestCase):
    def test_projection_left_metrics(self):
        # d(a,b)=a, ground=0
        code = encode_op([a for a in range(3) for b in range(3)])
        key = canonical_key(code)
        m = independent_metrics(key)
        self.assertEqual((m["d0"], m["d1"], m["d2"], m["d3"]), (3,3,3,3))
        self.assertEqual(m["recombinant3"], 0)
        self.assertEqual(m["recur_distinct_sum"], 15)
        self.assertEqual(m["recur_distinct_max"], 2)
        self.assertEqual(m["recur_cycle_sum"], 15)
        self.assertEqual(m["recur_cycle_max"], 2)

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


if __name__ == "__main__":
    unittest.main()
