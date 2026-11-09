import unittest

from silicon_professor.data.cores import CORES
from silicon_professor.data.nodes import NODES
from silicon_professor.data.tutorials import TUTORIAL_BY_ID
from silicon_professor.engine import ppa
from silicon_professor.engine.memory import memory_spec
from silicon_professor.engine.simulate import simulate
from silicon_professor.engine.types import Impl, empty_design
from silicon_professor.engine.wafer import wafer_sites


class TestEngineering(unittest.TestCase):
    def test_sram_scaled_once(self):
        for node in ("n7", "n3e"):
            area0 = ppa.core_area(CORES["x4"], Impl(), NODES[node], 0, False, 1)
            area1 = ppa.core_area(CORES["x4"], Impl(), NODES[node], 1, False, 1)
            self.assertAlmostEqual(area1 - area0, NODES[node]["sram_mb"])

    def test_memory_units_and_channels(self):
        d = empty_design("sandbox")
        d.memory_channels = 4
        self.assertAlmostEqual(memory_spec(d)["theoretical_gbs"], 68.264)
        a = simulate(d)
        d.memory_channels = 2
        d.placements.clear()
        b = simulate(d)
        self.assertAlmostEqual(b["engineering"]["memory"]["effective_gbs"] * 2,
                               a["engineering"]["memory"]["effective_gbs"])
        self.assertLess(b["die_area"], a["die_area"])
        self.assertLess(b["cost"]["dram"], a["cost"]["dram"])

    def test_capacity_and_cooling_are_platform_cost(self):
        d = empty_design("sandbox")
        a = simulate(d)
        d.memory_gb = 32
        d.cooling_id = "server"
        b = simulate(d)
        self.assertAlmostEqual(a["cost"]["total"], b["cost"]["total"])
        self.assertGreater(b["cost"]["platform_total"], a["cost"]["platform_total"])

    def test_serial_fraction_limits_scaling(self):
        d = empty_design("sandbox")
        d.workload_parallel = 0
        a = simulate(d)["engineering"]["workload"]
        self.assertAlmostEqual(a["amdahl_speedup"], 1)
        d.workload_parallel = .5
        b = simulate(d)["engineering"]["workload"]
        self.assertLess(b["amdahl_speedup"], 2)
        self.assertGreater(b["amdahl_speedup"], 1)

    def test_roofline_bottlenecks(self):
        d = empty_design("sandbox")
        d.workload_intensity = .1
        low = simulate(d)["engineering"]["workload"]
        d.workload_intensity = 16
        high = simulate(d)["engineering"]["workload"]
        self.assertEqual(low["bottleneck"], "内存带宽")
        self.assertEqual(high["bottleneck"], "计算 / 串行部分")
        self.assertLess(low["achievable"], high["achievable"])

    def test_pdn_and_verification_have_tradeoff(self):
        d = empty_design("laptop2025")
        d.pdn_quality = 0
        d.verification_effort = .1
        a = simulate(d)
        self.assertFalse(a["signoff"]["ready"])
        d.pdn_quality = 1
        d.verification_effort = 1
        b = simulate(d)
        self.assertGreater(b["nre"]["total"], a["nre"]["total"])
        self.assertLess(b["engineering"]["ir_drop_v"], a["engineering"]["ir_drop_v"])
        self.assertLess(b["market"]["p_crash"], a["market"]["p_crash"])
        self.assertTrue(b["signoff"]["ready"], b["signoff"]["blockers"])

    def test_high_frequency_cannot_hide_in_clamp(self):
        d = empty_design("laptop2025")
        d.cores[0].clock = 20
        r = simulate(d)
        self.assertLess(r["bin"]["fraction"], .01)
        self.assertFalse(r["signoff"]["ready"])
        self.assertTrue(any(c["id"] == "corner" for c in r["signoff"]["blockers"]))

    def test_full_rectangles_inside_wafer(self):
        d = empty_design("sandbox")
        r = simulate(d)
        p = r["plan"]
        sites = wafer_sites(p.die_w, p.die_h)
        self.assertEqual(len(sites), r["yield_"]["dies_per_wafer"])
        for x, y in sites:
            self.assertLessEqual((abs(x) + p.die_w / 2) ** 2 + (abs(y) + p.die_h / 2) ** 2, 147 ** 2)

    def test_new_lesson_is_solvable(self):
        lesson = TUTORIAL_BY_ID["t14"]
        d = lesson["make"]()
        a = simulate(d)
        self.assertFalse(all(s["check"](d, a) for s in lesson["steps"]))
        d.verification_effort = .8
        d.pdn_quality = 1
        for g in d.cores:
            g.clock *= .85
        b = simulate(d)
        self.assertTrue(all(s["check"](d, b) for s in lesson["steps"]), b["signoff"]["blockers"])

    def test_research_gpu_requires_sandbox(self):
        d = empty_design("flagship2022")
        d.gpu_id = "appleGpu"
        self.assertFalse(simulate(d)["valid"])
        d.scenario_id = "sandbox"
        self.assertTrue(simulate(d)["valid"])

    def test_finite_market(self):
        d = empty_design("sandbox")
        d.price = 1
        r = simulate(d)
        self.assertLessEqual(r["market"]["units"], r["scenario"]["base_units_m"] * 3)


if __name__ == "__main__":
    unittest.main()
