"""引擎单元与数值回归测试。运行：.venv/bin/python -m unittest discover -s tests -v"""
from __future__ import annotations

import copy
import unittest

from silicon_professor.data.cores import CORES, LICENSABLE
from silicon_professor.data.nodes import NODES
from silicon_professor.engine.build import build_plan
from silicon_professor.engine.simulate import simulate
from silicon_professor.data.cores import custom_ip
from silicon_professor.engine.types import CoreGroup, CustomCore, Design, Impl, empty_design


def clone(d: Design) -> Design:
    return Design.from_dict(d.to_dict())


class TestScenarios(unittest.TestCase):
    def test_all_scenarios_run_valid(self):
        for sid in ("mid2019", "flagship2022", "xring2025", "laptop2025", "sandbox"):
            with self.subTest(sid=sid):
                r = simulate(empty_design(sid))
                self.assertTrue(r["valid"], r["errors"])
                self.assertGreater(r["perf"]["st_burst"], 300)
                self.assertGreater(r["perf"]["mt_burst"], r["perf"]["st_burst"])
                self.assertGreater(r["die_area"], 20)
                self.assertGreater(r["yield_"]["yield_pct"], 0.2)
                self.assertGreater(r["cost"]["total"], 1)

    def test_xring_regression(self):
        r = simulate(empty_design("xring2025"))
        # 默认 2×X925 + 6×A725 + 2×A520 / N3E 的量级
        self.assertGreater(r["perf"]["st_burst"], 2500)
        self.assertLess(r["perf"]["st_burst"], 3100)
        self.assertGreater(r["perf"]["mt_burst"], 6000)
        self.assertLess(r["perf"]["mt_burst"], 8500)
        self.assertGreater(r["die_area"], 90)
        self.assertLess(r["die_area"], 150)
        self.assertGreater(r["yield_"]["yield_pct"], 0.55)

    def test_deterministic(self):
        d = empty_design("flagship2022")
        a = simulate(clone(d))
        b = simulate(clone(d))
        self.assertAlmostEqual(a["perf"]["st_burst"], b["perf"]["st_burst"], places=6)
        self.assertAlmostEqual(a["market"]["profit"], b["market"]["profit"], places=6)

    def test_repeated_simulate_same_design(self):
        d = empty_design("mid2019")
        a = simulate(d)
        b = simulate(d)
        c = simulate(d)
        self.assertAlmostEqual(a["die_area"], b["die_area"], places=6)
        self.assertAlmostEqual(b["die_area"], c["die_area"], places=6)
        self.assertTrue(b["valid"], b["errors"])


class TestFloorplan(unittest.TestCase):
    def test_auto_layout_no_overlap(self):
        for sid in ("mid2019", "flagship2022", "xring2025", "laptop2025"):
            with self.subTest(sid=sid):
                d = empty_design(sid)
                p = build_plan(d)
                self.assertEqual(p.metrics["overlaps"], 0, p.errors)
                self.assertTrue(p.fit, p.errors)

    def test_edge_blocks_on_edge(self):
        d = empty_design("flagship2022")
        p = build_plan(d)
        for b in p.blocks:
            if not b.edge:
                continue
            pl = p.placements[b.id]
            on_edge = (pl.x <= 0.8 or pl.y <= 0.8
                       or pl.x + pl.w >= p.die_w - 0.8 or pl.y + pl.h >= p.die_h - 0.8)
            self.assertTrue(on_edge, f"{b.label} not on edge")

    def test_utilization_reasonable(self):
        p = build_plan(empty_design("xring2025"))
        self.assertGreater(p.metrics["utilization"], 0.60)
        self.assertLess(p.metrics["utilization"], 0.98)

    def test_non_shared_l3_with_disabled_group(self):
        d = empty_design("flagship2022")
        d.cores[0].count = 0
        d.l3_shared = False
        r = simulate(d)
        self.assertTrue(r["valid"], r["errors"])
        self.assertFalse(any("l3:" in x for x in r["errors"]))

    def test_external_modem_trades_area_for_bom(self):
        d = empty_design("mid2019")
        self.assertEqual(d.modem_id, "modem_ext")
        integrated = clone(d)
        integrated.modem_id = "modem5g"
        a = simulate(d)
        b = simulate(integrated)
        self.assertLess(a["die_area"], b["die_area"])
        self.assertGreater(a["cost"]["total"], b["cost"]["total"])

    def test_die_grows_when_moving_block_far(self):
        d = empty_design("mid2019")
        p1 = build_plan(d)
        area1 = p1.die_area
        # 把 GPU 拖到很远的右下方
        pl = d.placements["gpu"]
        pl.x = p1.die_w + 5
        pl.y = p1.die_h + 5
        p2 = build_plan(d)
        self.assertGreater(p2.die_area, area1)


class TestMicroarchitecture(unittest.TestCase):
    def test_shared_l2_saves_area(self):
        d = empty_design("mid2019")
        a = clone(d)
        b = clone(d)
        a.cores[0].l2_shared = False
        b.cores[0].l2_shared = True
        pa = build_plan(a)
        pb = build_plan(b)
        self.assertLess(pb.used_area, pa.used_area)

    def test_more_big_cores_raise_mt(self):
        d = empty_design("flagship2022")
        one = clone(d)
        one.cores[0].count = 1
        four = clone(d)
        four.cores[0].count = 4
        r1 = simulate(one)
        r4 = simulate(four)
        self.assertGreater(r4["perf"]["mt_burst"], r1["perf"]["mt_burst"])

    def test_bigger_l3_raises_ipc(self):
        d = empty_design("flagship2022")
        small = clone(d)
        small.l3_mb = 2
        big = clone(d)
        big.l3_mb = 16
        rs = simulate(small)
        rb = simulate(big)
        self.assertGreater(rb["perf"]["st_burst"], rs["perf"]["st_burst"])

    def test_hvt_reduces_leakage_power(self):
        from silicon_professor.engine import ppa
        self.assertLess(ppa.impl_leak_factor(Impl(vt="hvt")),
                        ppa.impl_leak_factor(Impl(vt="svt")))
        d = empty_design("laptop2025")
        svt = clone(d)
        hvt = clone(d)
        hvt.cores[0].impl.vt = "hvt"
        rs = simulate(svt)
        rh = simulate(hvt)
        self.assertLess(rh["power"]["peak"], rs["power"]["peak"])

    def test_clock_above_fmax_lowers_bin(self):
        d = empty_design("flagship2022")
        low = clone(d)
        high = clone(d)
        low.cores[0].clock = 2.4
        high.cores[0].clock = 4.2
        rl = simulate(low)
        rh = simulate(high)
        self.assertGreater(rl["bin"]["fraction"], rh["bin"]["fraction"])
        self.assertGreater(rl["yield_"]["yield_pct"] * rl["bin"]["fraction"],
                           rh["yield_"]["yield_pct"] * rh["bin"]["fraction"])


class TestTuningAndMarket(unittest.TestCase):
    def test_benchmark_tuning_inflates_official_not_real(self):
        d = empty_design("xring2025")
        clean = clone(d)
        tuned = clone(d)
        tuned.bench_tuning = 0.9
        rc = simulate(clean)
        rt = simulate(tuned)
        self.assertGreater(rt["perf"]["official_st"], rc["perf"]["official_st"] * 1.1)
        self.assertLess(rt["perf"]["real_st"], rc["perf"]["real_st"])

    def test_benchmark_isa_inflates_official(self):
        d = empty_design("xring2025")
        clean = clone(d)
        isa = clone(d)
        isa.bench_isa = 0.7
        rc = simulate(clean)
        ri = simulate(isa)
        self.assertGreater(ri["perf"]["official_st"], rc["perf"]["official_st"] * 1.08)
        self.assertLess(abs(ri["perf"]["real_st"] - rc["perf"]["real_st"]), rc["perf"]["real_st"] * 0.2)
        self.assertGreater(ri["nre"]["total"], rc["nre"]["total"])

    def test_name_roundtrip(self):
        d = empty_design("mid2019")
        d.name = "我的中端 SoC"
        d2 = Design.from_dict(d.to_dict())
        self.assertEqual(d2.name, "我的中端 SoC")

    def test_caught_tuning_hurts_review(self):
        d = empty_design("xring2025")
        d.bench_tuning = 0.95
        seen = False
        for seed in range(12):
            x = clone(d)
            x.seed = seed
            r = simulate(x)
            if r["market"]["caught"]:
                seen = True
                self.assertLess(r["market"]["review"], 80)
        self.assertTrue(seen, "high tuning should be caught sometimes")

    def test_price_elasticity(self):
        d = empty_design("flagship2022")
        cheap = clone(d)
        pricey = clone(d)
        cheap.price = 70
        pricey.price = 130
        rc = simulate(cheap)
        rp = simulate(pricey)
        self.assertGreater(rc["market"]["units"], rp["market"]["units"])

    def test_disallowed_node_rejected(self):
        d = empty_design("mid2019")
        d.node_id = "n3e"
        r = simulate(d)
        self.assertFalse(r["valid"])
        self.assertTrue(any("制程范围" in e for e in r["errors"]))

    def test_research_core_locked(self):
        d = empty_design("flagship2022")
        d.cores = [CoreGroup("oryon", 4, 3.0, False, 3.8)]
        r = simulate(d)
        self.assertFalse(r["valid"])
        self.assertTrue(any("研究档案" in e for e in r["errors"]))

    def test_research_core_allowed_in_sandbox(self):
        d = empty_design("sandbox")
        d.cores = [CoreGroup("oryon", 4, 3.0, False, 3.8),
                   CoreGroup("oryon", 4, 3.0, False, 3.8)]
        r = simulate(d)
        # 沙盒允许研究核（混用同一核是合法的）
        self.assertFalse(any("研究档案" in e for e in r["errors"]))

    def test_isa_mix_rejected(self):
        d = empty_design("sandbox")
        d.cores = [CoreGroup("x4", 2, 2.0, False, 3.3),
                   CoreGroup("p670", 2, 0.5, False, 2.4)]
        r = simulate(d)
        self.assertTrue(any("RISC-V" in e and "混用" in e for e in r["errors"]))


class TestCustomCore(unittest.TestCase):
    def test_custom_core_runs(self):
        d = empty_design("sandbox")
        d.cores = [CoreGroup("custom", 2, 1.0, False, 3.6)]
        r = simulate(d)
        self.assertTrue(r["valid"], r["errors"])
        self.assertGreater(r["nre"]["custom"], 25)
        self.assertGreater(r["perf"]["st_burst"], 500)

    def test_wider_core_more_ipc_and_area(self):
        c1 = CustomCore(decode=4, rob=192, l1_kb=32, pipeline=12, backend=4)
        c2 = CustomCore(decode=10, rob=768, l1_kb=128, pipeline=10, backend=10)
        a = custom_ip(c1)
        b = custom_ip(c2)
        self.assertGreater(b["ipc"], a["ipc"])
        self.assertGreater(b["logic_area"], a["logic_area"])
        self.assertGreater(b["power_ref"], a["power_ref"])

    def test_chiplet_requires_25d_and_improves_yield(self):
        single = empty_design("laptop2025")
        chip = clone(single)
        chip.chiplet = True
        chip.package_id = "imc25d"
        rs = simulate(single)
        rc = simulate(chip)
        self.assertTrue(rc["valid"], rc["errors"])
        self.assertGreater(rc["yield_"]["yield_pct"], rs["yield_"]["yield_pct"])
        self.assertGreater(rc["cost"]["total"], rs["cost"]["total"])
        bad = clone(chip)
        bad.package_id = "pop"
        self.assertFalse(simulate(bad)["valid"])

    def test_custom_roundtrip(self):
        d = empty_design("sandbox")
        d.custom.decode = 9
        d2 = Design.from_dict(d.to_dict())
        self.assertEqual(d2.custom.decode, 9)


class TestPPA(unittest.TestCase):
    def test_denser_node_smaller_area(self):
        d = empty_design("sandbox")
        d.cores = [CoreGroup("x4", 2, 2.0, False, 3.2)]
        n5 = clone(d)
        n5.node_id = "n5"
        n3 = clone(d)
        n3.node_id = "n3e"
        a = build_plan(n5)
        b = build_plan(n3)
        self.assertLess(b.used_area, a.used_area)

    def test_hp_library_more_area_faster(self):
        d = empty_design("sandbox")
        d.cores = [CoreGroup("x925", 1, 2.0, False, 3.5)]
        sd = clone(d)
        hp = clone(d)
        hp.cores[0].impl = Impl(lib="hp", vt="lvt", density=0.2, timing=0.8, aspect=2)
        a = build_plan(sd)
        b = build_plan(hp)
        self.assertGreater(b.groups[0].fmax, a.groups[0].fmax)
        self.assertGreater(b.groups[0].area_each, a.groups[0].area_each)


if __name__ == "__main__":
    unittest.main()
