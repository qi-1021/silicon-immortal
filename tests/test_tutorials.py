"""教学关卡：每课目标可达、初始至少有一个未完成项。"""
from __future__ import annotations

import unittest

from silicon_professor.data.tutorials import TUTORIALS, TUTORIAL_BY_ID
from silicon_professor.engine.simulate import simulate
from silicon_professor.engine.types import Design


def fresh(tid: str) -> Design:
    return TUTORIAL_BY_ID[tid]["make"]()


def passed(tid: str, d: Design) -> tuple[bool, list[bool]]:
    r = simulate(d)
    res = [bool(s["check"](d, r)) for s in TUTORIAL_BY_ID[tid]["steps"]]
    return all(res), res


class TestTutorials(unittest.TestCase):
    def test_every_lesson_starts_with_work_to_do(self):
        for t in TUTORIALS:
            d = t["make"]()
            r = simulate(d)
            checks = [bool(s["check"](d, r)) for s in t["steps"]]
            self.assertFalse(all(checks), f"{t['id']} already solved at start")

    def test_t1_process(self):
        d = fresh("t1")
        d.node_id = "n5"
        d.placements.clear()
        ok, checks = passed("t1", d)
        self.assertTrue(ok, checks)

    def test_t2_power(self):
        d = fresh("t2")
        d.cores[0].clock = 2.4
        d.cores[1].clock = 2.2
        d.gpu_units = 8
        d.cooling_id = "vcPro"
        d.placements.clear()
        ok, checks = passed("t2", d)
        self.assertTrue(ok, checks)

    def test_t3_cache(self):
        d = fresh("t3")
        d.l3_mb = 12
        d.slc_mb = 8
        d.placements.clear()
        ok, checks = passed("t3", d)
        self.assertTrue(ok, checks)

    def test_t4_physical(self):
        d = fresh("t4")
        g = d.cores[0]
        g.clock = 3.9
        g.impl.lib = "hp"
        g.impl.vt = "lvt"
        g.impl.timing = 0.8
        g.impl.density = 0.2
        d.placements.clear()
        ok, checks = passed("t4", d)
        self.assertTrue(ok, checks)

    def test_t5_layout_auto(self):
        d = fresh("t5")
        d.placements.clear()
        ok, checks = passed("t5", d)
        self.assertTrue(ok, checks)

    def test_t6_benchmark(self):
        d = fresh("t6")
        d.bench_tuning = 0.3
        ok, checks = passed("t6", d)
        self.assertTrue(ok, checks)

    def test_t8_gpu_npu(self):
        d = fresh("t8")
        d.gpu_units = 12
        d.npu_id = "none"
        d.placements.clear()
        ok, checks = passed("t8", d)
        self.assertTrue(ok, checks)

    def test_t9_memory(self):
        d = fresh("t9")
        d.dram = "lpddr5x"
        d.modem_id = "modem5g"
        d.placements.clear()
        ok, checks = passed("t9", d)
        self.assertTrue(ok, checks)

    def test_t10_layout(self):
        d = fresh("t10")
        d.media = False
        d.placements.clear()
        simulate(d)
        d.rotated_once = True
        d.placements.clear()
        ok, checks = passed("t10", d)
        self.assertTrue(ok, checks)

    def test_t11_riscv(self):
        d = fresh("t11")
        d.eco_invest = 1.0
        d.placements.clear()
        ok, checks = passed("t11", d)
        self.assertTrue(ok, checks)

    def test_t12_failure_modes(self):
        d = fresh("t12")
        ok, checks = passed("t12", d)
        self.assertFalse(ok, f"should start unsolved, got {checks}")
        d.cores[0].clock = 3.3
        d.bench_tuning = 0.2
        d.cooling_id = "vc"
        d.ambient_c = 25
        d.gpu_units = 11
        d.pdn_quality = 1.0
        ok, checks = passed("t12", d)
        self.assertTrue(ok, checks)

    def test_t13_accessories(self):
        d = fresh("t13")
        ok, checks = passed("t13", d)
        self.assertFalse(ok, f"should start unsolved, got {checks}")
        d.cores[2].count = 4
        d.storage_id = "ufs31"
        d.modem_id = "modem5g"
        d.placements.clear()
        ok, checks = passed("t13", d)
        self.assertTrue(ok, checks)

    def test_t13_accessories(self):
        d = fresh("t13")
        ok, checks = passed("t13", d)
        self.assertFalse(ok, f"should start unsolved, got {checks}")
        d.cores[2].count = 4
        d.storage_id = "ufs31"
        d.modem_id = "modem5g"
        d.placements.clear()
        ok, checks = passed("t13", d)
        self.assertTrue(ok, checks)

    def test_prototype_cost_and_risk_regression(self):
        # 仅比较两个未核验沙盒输入的内部模型结果，不代表真实产品结论。
        from silicon_professor.ui.main_window import MainWindow
        from silicon_professor.ui import theme as T
        from PySide6.QtWidgets import QApplication
        from silicon_professor.data.blueprints import BLUEPRINT_BY_ID
        app = QApplication.instance() or QApplication([])
        app.setStyle("Fusion"); app.setStyleSheet(T.QSS)
        w = MainWindow()
        outs = {}
        for bid in ("sd8elite5", "sd8elite6"):
            w.load_blueprint_as_design(BLUEPRINT_BY_ID[bid])
            w.recompute_now()
            outs[bid] = w.result
        e5, e6 = outs["sd8elite5"]["market"], outs["sd8elite6"]["market"]
        self.assertGreater(e6["p_crash"], e5["p_crash"])
        self.assertLess(e6["profit"], e5["profit"])
        self.assertGreater(outs["sd8elite6"]["cost"]["total"], outs["sd8elite5"]["cost"]["total"])

    def test_t7_price(self):
        d = fresh("t7")
        d.price = 90
        ok, checks = passed("t7", d)
        self.assertTrue(ok, checks)


if __name__ == "__main__":
    unittest.main()
