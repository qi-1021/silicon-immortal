from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from silicon_professor import export
from silicon_professor.engine.simulate import simulate
from silicon_professor.engine.types import empty_design


class TestExport(unittest.TestCase):
    def test_payload_and_file(self):
        d = empty_design("xring2025")
        d.name = "测试芯片 X1"
        r = simulate(d)
        p = export.payload(d, r)
        self.assertEqual(p["format"], export.FORMAT)
        self.assertEqual(p["version"], export.VERSION)
        self.assertEqual(p["name"], "测试芯片 X1")
        self.assertEqual(p["design"]["scenario_id"], "xring2025")
        self.assertIn("placements", p["design"])
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "x.spchip.json"
            export.export_to(path, d, r)
            data = json.loads(path.read_text("utf-8"))
            self.assertEqual(data["design"]["name"], "测试芯片 X1")
            self.assertTrue(data["summary"]["valid"])


if __name__ == "__main__":
    unittest.main()
