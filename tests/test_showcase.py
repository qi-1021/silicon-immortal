"""展示页与 Die Shot 导出冒烟测试（offscreen）。"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from silicon_professor import export
from silicon_professor import save as savemod
from silicon_professor.data.blueprints import BLUEPRINT_BY_ID
from silicon_professor.engine.types import empty_design
from silicon_professor.engine.simulate import simulate
from silicon_professor.ui import anim, theme as T
from silicon_professor.ui.main_window import MainWindow


def _app():
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(T.QSS)
    return app


class TestShowcase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = _app()
        anim.set_enabled(False)

    @classmethod
    def tearDownClass(cls):
        anim.set_enabled(True)

    def setUp(self):
        self.savedir = tempfile.TemporaryDirectory()
        self.addCleanup(self.savedir.cleanup)
        self.savepatch = patch.multiple(savemod, SAVE_DIR=Path(self.savedir.name),
                                       SAVE_PATH=Path(self.savedir.name) / "save.json")
        self.savepatch.start()
        self.addCleanup(self.savepatch.stop)

    def settle(self):
        from PySide6.QtCore import QCoreApplication, QEvent
        for _ in range(5):
            self.app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_showcase_refresh(self):
        w = MainWindow()
        w.start_scenario("xring2025")
        w.recompute_now()
        w.go("showcase")
        s = w.screens["showcase"]
        px = s.die.pixmap()
        self.assertIsNotNone(px)
        self.assertFalse(px.isNull())
        self.assertIn("@", s.spec.text())

    def test_dieshot_export(self):
        d = empty_design("mid2019")
        r = simulate(d)
        with tempfile.TemporaryDirectory() as td:
            p = export.export_dieshot_png(f"{td}/t.png", d, r, width=800)
            self.assertTrue(p.exists())
            self.assertGreater(p.stat().st_size, 20000)

    def test_replica_showcase(self):
        w = MainWindow()
        w.load_blueprint_as_design(BLUEPRINT_BY_ID["xringO3"])
        w.design.pdn_quality = 1.0
        w.recompute_now()
        w.tape_out()
        self.assertEqual(w.stack.currentWidget(), w.screens["showcase"])
        self.assertFalse(w.screens["showcase"].die.pixmap().isNull())

    def test_showcase_modes_and_recompute(self):
        w = MainWindow()
        self.addCleanup(w.close)
        w.start_scenario("sandbox")
        w.go("showcase")
        s = w.screens["showcase"]
        for mode in ("silicon", "wafer", "layout"):
            s.views.select(mode)
            self.assertFalse(s.die.pixmap().isNull(), mode)
        self.assertEqual(set(s.views.buttons), {"silicon", "wafer", "layout"})
        s.views.select("silicon")
        old = s.stats["st"].v.text()
        w.design.cores[0].clock *= .7
        w.recompute_now()
        self.assertNotEqual(old, s.stats["st"].v.text())
        self.assertIn("设计预览", s.status.text())

    def test_tape_out_matches_ui_checks(self):
        w = MainWindow()
        self.addCleanup(w.close)
        w.start_scenario("sandbox")
        w.design.verification_effort = 0
        w.go("signoff")
        w.recompute_now()
        self.assertFalse(w.screens["signoff"].tape.isEnabled())
        w.tape_out()
        self.assertEqual(w.stack.currentWidget(), w.screens["signoff"])
        w.design.verification_effort = 1
        w.design.pdn_quality = 1
        w.recompute_now()
        self.assertTrue(w.screens["signoff"].tape.isEnabled())
        w.tape_out()
        self.assertTrue(w.is_released)
        w.design.price += 1
        self.assertFalse(w.is_released)

    def test_filter_opens_selected_chip_and_empty_state(self):
        w = MainWindow()
        self.addCleanup(w.close)
        w.go("codex")
        s = w.screens["codex"]
        s.filter.setText("Tensor G4")
        self.assertEqual(s.list.count(), 1)
        labels = s.page.findChildren(QLabel)
        self.assertTrue(any(l.text() == "Google Tensor G4" for l in labels))
        s.filter.setText("no_such_chip_123")
        self.assertEqual(s.list.count(), 0)

    def test_compact_layout_and_canvas(self):
        w = MainWindow()
        self.addCleanup(w.close)
        w.resize(1180, 760)
        w.show()
        w.start_scenario("sandbox")
        w.go("architecture")
        self.settle()
        for row in w.screens["architecture"].rows:
            self.assertGreaterEqual(row["combo"].height(), 30)
        w.go("showcase")
        self.settle()
        s = w.screens["showcase"]
        self.assertGreater(s.die.height(), s.hero.height() * .7)

    def test_all_simulated_exports(self):
        d = empty_design("sandbox")
        r = simulate(d)
        with tempfile.TemporaryDirectory() as td:
            for mode in ("silicon", "wafer", "layout"):
                path = export.export_dieshot_png(f"{td}/{mode}.png", d, r, width=800, mode=mode)
                self.assertGreater(path.stat().st_size, 20000)
            with self.assertRaises(ValueError):
                export.export_dieshot_png(f"{td}/ref.png", d, r, mode="reference")


if __name__ == "__main__":
    unittest.main()
