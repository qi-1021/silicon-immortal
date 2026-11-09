import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from silicon_professor import save
from silicon_professor.ui.main_window import MainWindow


class TestRescueUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup)
        p=patch.multiple(save,SAVE_DIR=Path(td.name),SAVE_PATH=Path(td.name)/'save.json')
        p.start();self.addCleanup(p.stop)
        self.win=MainWindow();self.addCleanup(self.win.close)

    def test_entry_needs_no_soc_and_reference_does_not_auto_complete(self):
        w=self.win;w.rescue_button.click();s=w.screens['rescue']
        self.assertIs(w.stack.currentWidget(),s);self.assertIsNone(w.design)
        s.select_case('rescue_fdiv');s.run();self.assertFalse(s.finish_btn.isEnabled())
        s.load_reference();self.assertTrue(s.last_result['ready'])
        self.assertNotIn('rescue_fdiv',w.progress.get('rescues',{}))
        s.complete();self.assertTrue(w.progress['rescues']['rescue_fdiv']['completed'])
        again=MainWindow();self.addCleanup(again.close)
        self.assertTrue(again.progress['rescues']['rescue_fdiv']['completed'])

    def test_parameters_restore_and_changes_invalidate_last_acceptance(self):
        s=self.win.screens['rescue'];s.select_case('rescue_fdiv');s.load_reference()
        s.controls['divider'].setCurrentIndex(s.controls['divider'].findData('software'))
        self.assertIsNone(s.last_result);self.assertFalse(s.finish_btn.isEnabled())
        s.select_case('rescue_888');s.select_case('rescue_fdiv')
        self.assertEqual(s.controls['divider'].currentData(),'software')
        again=MainWindow();self.addCleanup(again.close)
        self.assertEqual(again.screens['rescue'].controls['divider'].currentData(),'software')

    def test_related_lab_experiment_and_project_are_independent(self):
        w=self.win;w.start_scenario('x86_workstation');design=w.design.to_dict()
        s=w.screens['rescue'];s.select_case('rescue_barcelona')
        s.lab_picker.setCurrentIndex(s.lab_picker.findData('smt'));s.open_lab()
        studio=w.screens['studio'];self.assertEqual(studio.current['hardware']['smt_threads'],2)
        self.assertEqual(len(studio.last_result['threads']),2)
        self.assertEqual(w.design.to_dict(),design)

    def test_each_case_shows_conditions_sources_and_model_boundary(self):
        s=self.win.screens['rescue']
        for cid in ('rescue_810','rescue_888','rescue_tensor_g6'):
            s.select_case(cid)
            self.assertIn('芯片本体',s.case_text.toPlainText())
            self.assertIn('不是反事实预测',s.case_text.toPlainText())
            s.load_reference();self.assertFalse(s.last_result['ready'])
            self.assertFalse(s.finish_btn.isEnabled())
            self.assertTrue(s.parameter_scroll.isHidden())
            self.assertTrue(s.reference_btn.isHidden())
