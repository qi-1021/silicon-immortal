"""数据完整性与引用检查。"""
from __future__ import annotations

import unittest

from silicon_professor.data.blueprints import BLUEPRINTS
from silicon_professor.data.blocks import (COOLING, DRAMS, FIXED_BLOCKS, GPUS,
                                           METAL_STACKS, NOCS, NPUS, PACKAGES)
from silicon_professor.data.cores import CORES
from silicon_professor.data.nodes import NODES
from silicon_professor.data.segments import SEGMENTS
from silicon_professor.data.sources import SOURCES, TIER_LABELS


class TestData(unittest.TestCase):
    def test_all_evidence_exists(self):
        groups = [NODES.values(), CORES.values(), GPUS.values(), NPUS.values(),
                  FIXED_BLOCKS.values(), NOCS.values(), PACKAGES.values(),
                  COOLING.values(), SEGMENTS.values(), BLUEPRINTS]
        for group in groups:
            for item in group:
                for sid in item.get("evidence", []):
                    self.assertIn(sid, SOURCES, f"{item.get('id') or item.get('name')} -> {sid}")

    def test_core_ref_nodes(self):
        for c in CORES.values():
            self.assertIn(c["ref_node"], NODES, c["id"])
            self.assertGreater(c["ipc"], 0)
            self.assertGreater(c["fmax_ref"], 0)
            self.assertGreater(c["logic_area"], 0)
            self.assertGreaterEqual(c["l2_max"], c["l2_default"])
            self.assertIn(c["tier"], ("big", "mid", "little"))
            self.assertIn(c["license"], ("arm", "riscv", "research"))

    def test_blueprint_nodes(self):
        for b in BLUEPRINTS:
            self.assertIn(b["node"], NODES, b["id"])
            self.assertGreater(b["die_area"], 10)
            self.assertTrue(b.get("layout"))

    def test_segment_nodes(self):
        for s in SEGMENTS.values():
            for n in s["allowed_nodes"]:
                self.assertIn(n, NODES, s["id"])
            for k in ("st", "mt", "gpu", "ai", "battery_h"):
                self.assertIn(k, s["targets"])
            self.assertIn("max_die_area", s["limits"])

    def test_source_tiers(self):
        for sid, s in SOURCES.items():
            self.assertIn(s["tier"], TIER_LABELS, sid)
            self.assertTrue(s["title"])

    def test_gpu_units(self):
        for g in GPUS.values():
            self.assertLessEqual(g["min_units"], g["default_units"])
            self.assertLessEqual(g["default_units"], g["max_units"])

    def test_dram_bandwidth_plausible(self):
        for d in DRAMS.values():
            gbs = d["gbps"] * d["channels"] * 2 / 1000 * d["efficiency"]
            self.assertGreater(gbs, 5)
            self.assertLess(gbs, 120)

    def test_metal_area_overhead(self):
        for m in METAL_STACKS.values():
            self.assertGreater(m["area_overhead"], 0.05)
            self.assertLess(m["area_overhead"], 0.4)


if __name__ == "__main__":
    unittest.main()
