from __future__ import annotations

import unittest

from silicon_professor.search_index import INDEX, search


class TestSearch(unittest.TestCase):
    def test_index_covers_all_content(self):
        kinds = {x["kind"] for x in INDEX}
        self.assertTrue({"chip", "core", "source", "tutorial", "node", "gpu"} <= kinds)

    def test_find_xring(self):
        hits = search("XRING")
        self.assertTrue(any(h["id"] == "xringO3" for h in hits))

    def test_find_riscv_core(self):
        hits = search("RISC-V")
        self.assertTrue(any(h["kind"] == "core" and "risc" in h["subtitle"].lower() for h in hits))

    def test_find_source_tier(self):
        hits = search("CACTI")
        self.assertTrue(any(h["kind"] == "source" for h in hits))


if __name__ == "__main__":
    unittest.main()
