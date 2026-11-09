import unittest
from silicon_professor.engine.geekbench import measured_geekbench6,compose_geekbench6,projected_geekbench6


class TestGeekbench(unittest.TestCase):
    def test_measured_major_versions_do_not_confuse_gb5_with_gb6(self):
        r=measured_geekbench6('rescue_tensor_g2')[0]
        self.assertEqual(r['version'],'6.7');self.assertEqual(r['value'],dict(single=1465,multi=3967))
        self.assertNotEqual(r['value']['single'],1048)
        self.assertEqual(measured_geekbench6('rescue_810'),[])
        self.assertEqual(measured_geekbench6('rescue_888'),[])

    def test_score_composition_follows_subsection_geometric_and_composite_arithmetic(self):
        self.assertAlmostEqual(compose_geekbench6([1000,4000],[2000,8000]),.65*2000+.35*4000)
        with self.assertRaises(ValueError):compose_geekbench6([],[])
        with self.assertRaises(ValueError):compose_geekbench6([True],[1])

    def test_uncalibrated_design_never_gets_fake_geekbench_score(self):
        r=projected_geekbench6();self.assertFalse(r['available']);self.assertIsNone(r['score'])
        r=projected_geekbench6([2500]*10,[2500]*6)
        self.assertTrue(r['available']);self.assertAlmostEqual(r['score'],2500)
        self.assertFalse(r['official'])
