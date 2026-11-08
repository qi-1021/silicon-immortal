import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtWidgets import QApplication
from silicon_professor import save
from silicon_professor.ui import anim, theme as T
from silicon_professor.ui.main_window import MainWindow
from silicon_professor.data.lab_courses import COURSES


class TestLabsUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.app.setStyle('Fusion');cls.app.setFont(T.font(13));cls.app.setStyleSheet(T.QSS)
        anim.set_enabled(False)

    def setUp(self):
        directory=tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.patch=patch.multiple(save,SAVE_DIR=Path(directory.name),SAVE_PATH=Path(directory.name)/'save.json')
        self.patch.start();self.addCleanup(self.patch.stop)
        self.window=MainWindow();self.addCleanup(self.window.close)

    def test_switch_experiments_and_run_without_design(self):
        w=self.window;w.go('labs');s=w.screens['labs']
        for kind in ('cpu','cache','network','timing','power','logic','cpu'):
            s.kind_picker.setCurrentIndex(s.kind_picker.findData(kind));s.run()
            self.assertIsNotNone(s.last_result,kind)
            self.assertFalse(s.apply_btn.isEnabled())

    def test_courses_complete_only_after_running(self):
        s=self.window.screens['labs']
        for course in COURSES:
            s.select_course(course['id']);s._load_solution()
            self.assertNotIn(course['id'],self.window.progress.get('lab_courses',{}))
            s.run()
            self.assertTrue(self.window.progress['lab_courses'][course['id']])

    def test_apply_runs_core_and_serializes_extensions(self):
        w=self.window;w.start_scenario('sandbox');w.go('labs');s=w.screens['labs']
        s.asset_name.setText('实验核心');s.replace_cpu.setChecked(True)
        s.run();self.assertTrue(s.apply_btn.isEnabled());s._apply()
        self.assertEqual(w.result['groups'][0]['ip']['isa'],'riscv')
        self.assertTrue(w.design.cores[0].core_id.startswith('ip:'))
        self.assertIn('measured_ipc',w.result['groups'][0]['ip'])
        self.assertEqual(next(iter(w.design.embedded_ips.values()))['config']['extensions'],['M'])

    def test_modes_fold_parameters_without_changing_inputs(self):
        w=self.window;s=w.screens['labs'];before=s.inputs()
        for mode in ('beginner','intermediate','advanced','professional'):
            w.mode_picker.setCurrentIndex(w.mode_picker.findData(mode))
            self.assertEqual(s.inputs(),before)

    def test_x86_and_accelerators_run_save_and_reload(self):
        w=self.window;s=w.screens['labs']
        s.controls['architecture'].setCurrentIndex(s.controls['architecture'].findData('x86_32'))
        s.run();self.assertEqual(s.last_result['architecture'],'x86_32')
        s.asset_name.setText('x86 mine');asset=s._save_ip();self.assertIsNotNone(asset)
        for kind in ('gpu','npu','isp'):
            s.kind_picker.setCurrentIndex(s.kind_picker.findData(kind));s.run()
            self.assertIsNotNone(s.last_result,kind);s.asset_name.setText(kind+' mine');self.assertIsNotNone(s._save_ip())
        again=MainWindow();self.addCleanup(again.close)
        self.assertEqual(len(again.ip_library),4)

    def test_native_architecture_catalog_opens_sources_and_hides_rv_extensions(self):
        from PySide6.QtWidgets import QPushButton
        s=self.window.screens['labs']
        buttons={b.property('source_id'):b for b in s.findChildren(QPushButton) if b.property('source_id')}
        self.assertIn('intel_ia32',buttons);self.assertIn('arm_a64_isa',buttons)
        with patch('silicon_professor.ui.screens.labs.InfoDialog.exec',return_value=0) as show:
            buttons['intel_ia32'].click();buttons['arm_a64_isa'].click()
            self.assertEqual(show.call_count,2)
        for architecture in ('x86_32','aarch64'):
            s.controls['architecture'].setCurrentIndex(s.controls['architecture'].findData(architecture))
            self.assertTrue(all(c.isHidden() for c in s.ext_checks.values()))
            self.assertEqual(s.inputs()['extensions'],[])

    def test_register_replay(self):
        s=self.window.screens['labs'];s.run()
        s.replay.setValue(0)
        self.assertEqual(s.register_table.item(1,2).text(),'0')
        s.replay.setValue(s.last_result['cycles'])
        self.assertEqual(s.register_table.item(1,2).text(),'42')

    def test_cpu_draft_survives_restart_without_a_design(self):
        w=self.window;s=w.screens['labs']
        s.editors['source'].setPlainText('ADDI x1,x0,77\nHALT')
        reopened=MainWindow();self.addCleanup(reopened.close)
        self.assertEqual(reopened.screens['labs'].editors['source'].toPlainText(),'ADDI x1,x0,77\nHALT')

    def test_bad_program_and_modified_input_invalidate_results(self):
        s=self.window.screens['labs'];s.run()
        s.editors['source'].setPlainText('ADDI x1,x0,4096');self.assertIsNone(s.last_result)
        s.run();self.assertIn('实验未完成',s.summary.text());self.assertFalse(s.export_btn.isEnabled())

    def test_brand_copy_and_soc_import(self):
        from PySide6.QtWidgets import QLabel
        from silicon_professor import export
        w=self.window
        labels=[x.text() for x in w.screens['start'].findChildren(QLabel)]
        for text in ('a simulate silicon designer for everyone','一个人尽可用的芯片设计模拟器','powered by isqi'):
            self.assertTrue(any(text in s for s in labels))
        self.assertTrue(any("don't take this for real one,it is just a game" in s for s in labels))
        w.start_scenario('sandbox');w.design.name='file chip'
        with tempfile.TemporaryDirectory() as td:
            path=export.export_to(Path(td)/'file.sil',w.design,w.result)
            w.start_scenario('mid2019');w.import_soc(str(path))
            self.assertEqual(w.design.name,'file chip')


if __name__=='__main__':unittest.main()
