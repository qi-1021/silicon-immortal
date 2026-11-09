import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from silicon_professor import save
from silicon_professor.ui.main_window import MainWindow


class TestObservatoryUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup)
        p=patch.multiple(save,SAVE_DIR=Path(td.name),SAVE_PATH=Path(td.name)/'save.json')
        p.start();self.addCleanup(p.stop)
        self.win=MainWindow();self.addCleanup(self.win.close)

    def test_all_four_kinds_can_scrub_to_actual_output_and_step_back(self):
        s=self.win.screens['studio']
        for kind in ('cpu','gpu','npu','isp'):
            s.new_design(kind);s.run_bench()
            observer=s.observer
            self.assertIsNotNone(observer,kind)
            self.assertIn('执行观测',[s.tabs.tabText(i) for i in range(s.tabs.count())])
            observer.cycle.setValue(s.last_result['cycles'])
            self.assertEqual(observer.snapshot['phase'],'完成')
            observer.step(-1)
            self.assertEqual(observer.cycle.value(),s.last_result['cycles']-1)
            observer.toggle_play();self.assertTrue(observer.timer.isActive())
            observer.toggle_play();self.assertFalse(observer.timer.isActive())

    def test_smt_thread_choice_and_draft_change_clear_stale_replay(self):
        s=self.win.screens['studio']
        s.controls['smt_threads'].setCurrentIndex(s.controls['smt_threads'].findData(2))
        s.bench_controls['source2'].setPlainText('ADDI x1,x0,9\nHALT')
        s.run_bench();o=s.observer
        self.assertIn('双线程对比',s.test_summary.text())
        o.thread.setCurrentIndex(1);o.cycle.setValue(s.last_result['cycles'])
        self.assertEqual(o.snapshot['registers'][1],9)
        o.toggle_play();self.assertTrue(o.timer.isActive())
        s.bench_controls['source2'].setPlainText('HALT')
        self.assertIsNone(s.observer)
        self.assertFalse(o.timer.isActive())

    def test_isp_stage_picker_changes_image_data_not_hardware(self):
        s=self.win.screens['studio'];s.new_design('isp');s.run_bench();o=s.observer
        hardware=dict(s.current['hardware'])
        o.stage.setCurrentIndex(o.stage.findData('raw'))
        self.assertEqual(o.selected_stage,'raw')
        self.assertEqual(s.current['hardware'],hardware)
