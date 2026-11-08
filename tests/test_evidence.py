import json
import unittest
from pathlib import Path

from silicon_professor.data.sources import SOURCES


class TestEvidence(unittest.TestCase):
    def test_each_source_has_explicit_scope_and_locator(self):
        for sid, source in SOURCES.items():
            with self.subTest(source=sid):
                for field in ("locator", "supports", "does_not_support", "model_use", "verification", "audit"):
                    self.assertTrue(source.get(field), f"{sid}: {field}")
                self.assertIn(source["verification"], ("fulltext_checked", "bibliography_checked"))
                self.assertTrue(source["url"].startswith("https://"))

    def test_murphy_wrong_doi_is_removed(self):
        self.assertIn("3442", SOURCES["murphy1964"]["url"])
        self.assertNotIn("2992", SOURCES["murphy1964"]["url"])
        self.assertEqual(SOURCES["murphy1964"]["verification"], "bibliography_checked")

    def test_every_legacy_source_has_a_disposition(self):
        root = Path(__file__).resolve().parents[1]
        legacy = json.loads((root / "docs/research/legacy_sources.json").read_text(encoding="utf-8"))
        audit = json.loads((root / "docs/research/audit.json").read_text(encoding="utf-8"))
        self.assertEqual(set(legacy), set(audit["legacy"]))
        for source in audit["legacy"].values():
            self.assertTrue(source["reason"])
            self.assertIn(source["disposition"], ("corrected", "replaced", "withdrawn"))

    def test_parameter_estimates_cannot_claim_a_paper(self):
        from silicon_professor.data.cores import CORES
        from silicon_professor.data.nodes import NODES
        for item in list(CORES.values()) + list(NODES.values()):
            self.assertEqual(item["parameter_basis"], "game_assumption")
            for evidence in item.get("evidence", []):
                self.assertIn(evidence, SOURCES)


if __name__ == "__main__": unittest.main()
