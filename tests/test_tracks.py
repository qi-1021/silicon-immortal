"""ISA 赛道：ARM / RISC-V 独立，x86 桩位预留。"""
from __future__ import annotations

import unittest

from silicon_professor.data.cores import CORES
from silicon_professor.data.tracks import TRACKS, design_track, track_of_isa
from silicon_professor.engine.simulate import simulate
from silicon_professor.engine.types import CoreGroup, empty_design


def _with_cores(design, *cids):
    from silicon_professor.data.cores import get_ip
    design.cores = []
    for cid in cids:
        ip = get_ip(design, cid)
        design.cores.append(CoreGroup(cid, 2, ip["l2_default"], False, 0.0))
    design.placements.clear()
    return design


class TestTracks(unittest.TestCase):
    def test_isa_mapping(self):
        self.assertEqual(track_of_isa("armv9"), "arm")
        self.assertEqual(track_of_isa("armv8"), "arm")
        self.assertEqual(track_of_isa("riscv"), "riscv")
        self.assertEqual(track_of_isa("x86_64"), "x86")

    def test_x86_experiment_track_available(self):
        self.assertIn("x86", TRACKS)
        self.assertTrue(TRACKS["x86"]["available"])

    def test_all_cores_map_to_tracks(self):
        for c in CORES.values():
            self.assertIn(track_of_isa(c["isa"]), TRACKS, c["id"])

    def test_design_track(self):
        d = empty_design("sandbox")
        d = _with_cores(d, "x4", "a720")
        self.assertEqual(design_track(d), "arm")
        d = _with_cores(d, "p670", "p870")
        self.assertEqual(design_track(d), "riscv")
        d = _with_cores(d, "x4", "p670")
        self.assertEqual(design_track(d), "mixed")
        d.cores = []
        self.assertIsNone(design_track(d))

    def test_riscv_eco_uses_track_params(self):
        d = empty_design("sandbox")
        d = _with_cores(d, "p670")
        d.eco_invest = 0.0
        r = simulate(d)
        self.assertAlmostEqual(r["market"]["eco"], TRACKS["riscv"]["eco_base"], places=6)
        d.eco_invest = 1.0
        r = simulate(d)
        self.assertAlmostEqual(
            r["market"]["eco"], TRACKS["riscv"]["eco_base"] + TRACKS["riscv"]["eco_gain"], places=6)

    def test_arm_eco_unaffected(self):
        d = empty_design("sandbox")
        d = _with_cores(d, "x4")
        r = simulate(d)
        self.assertAlmostEqual(r["market"]["eco"], 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
