import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from silicon_professor import save
from silicon_professor.ui import theme as T
from silicon_professor.ui.main_window import MainWindow


class TestSandboxUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.app.setStyle('Fusion');cls.app.setStyleSheet(T.QSS)

    def test_free_and_product_workspaces_are_independent_and_survive_restart(self):
        with tempfile.TemporaryDirectory() as td,patch.multiple(save,SAVE_DIR=Path(td),SAVE_PATH=Path(td)/'save.json'):
            w=MainWindow()
            try:
                w.start_scenario('x86_workstation');w.design.name='我的产品';w.persist()
                w.start_sandbox();w.design.name='自由研究';w.design.pdn_resistance_mohm=200;w.recompute_now()
                self.assertEqual(w.stack.currentWidget(),w.screens['sandbox'])
                self.assertTrue(w.result['signoff']['ready']);self.assertTrue(w.result['signoff']['diagnostics'])
                w.return_to_project();self.assertEqual(w.design.name,'我的产品')
                w.start_sandbox();self.assertEqual(w.design.name,'自由研究');w.persist()
                again=MainWindow()
                try:
                    again.return_to_project();self.assertEqual(again.design.name,'我的产品')
                    again.start_sandbox();self.assertEqual(again.design.pdn_resistance_mohm,200)
                finally:again.close()
            finally:w.close()

    def test_pdn_control_updates_design_and_headers_align_with_rows(self):
        with tempfile.TemporaryDirectory() as td,patch.multiple(save,SAVE_DIR=Path(td),SAVE_PATH=Path(td)/'save.json'):
            w=MainWindow()
            try:
                w.start_scenario('mid2019');w.go('architecture');w.show();self.app.processEvents()
                architecture=w.screens['architecture'];row=architecture.rows[0]
                # Shared grid headers and controls have exactly the same fixed numeric columns.
                self.assertEqual(row['count'].width(),66);self.assertEqual(row['l2'].width(),106)
                self.assertEqual(row['shared'].width(),96);self.assertEqual(row['clock'].width(),116)
                self.assertEqual(row['shared'].currentText(),'每核私有')
                w.go('engineering');e=w.screens['engineering'];e.pdn_resistance.setValue(5.5);w.recompute_now()
                self.assertEqual(w.design.pdn_resistance_mohm,5.5)
                self.assertAlmostEqual(w.result['engineering']['pdn_resistance_ohm'],.0055)
            finally:w.close()
