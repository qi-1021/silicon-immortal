import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from silicon_professor import save
from silicon_professor.ui import anim,theme as T
from silicon_professor.ui.main_window import MainWindow
from silicon_professor.engine.ip_library import read_asset,write_asset,make_design_asset,attach_asset
from silicon_professor.data.core_designs import default_hardware
from silicon_professor import export
from silicon_professor.engine.types import empty_design
from silicon_professor.data.cores import CORES
from silicon_professor.data.blocks import GPUS,NPUS


class TestStudioUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.app.setStyle('Fusion');cls.app.setFont(T.font(13));cls.app.setStyleSheet(T.QSS)
        anim.set_enabled(False)

    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.patch=patch.multiple(save,SAVE_DIR=Path(directory.name),SAVE_PATH=Path(directory.name)/'save.json')
        self.patch.start();self.addCleanup(self.patch.stop)
        self.window=MainWindow();self.addCleanup(self.window.close)

    def test_default_lab_destination_is_design_without_courses(self):
        w=self.window;w.studio_button.click()
        s=w.screens['studio'];self.assertIs(w.stack.currentWidget(),s)
        self.assertEqual(s.tabs.currentIndex(),0)
        self.assertFalse(hasattr(s,'courses'))
        self.assertIsNone(w.design)
        self.assertEqual(s.current['kind'],'cpu')

    def test_create_four_named_designs_and_restore_editable_hardware(self):
        s=self.window.screens['studio']
        for kind in ('cpu','gpu','npu','isp'):
            s.new_design(kind);s.name_edit.setText('我的 '+kind)
        s.controls['demosaic_enabled'].setChecked(False)
        again=MainWindow();self.addCleanup(again.close)
        restored=again.screens['studio']
        self.assertEqual(restored.current['name'],'我的 isp')
        self.assertFalse(restored.current['hardware']['demosaic_enabled'])
        self.assertGreaterEqual(len(again.core_workspace['drafts']),4)

    def test_verification_then_publish_is_independent_of_testbench(self):
        s=self.window.screens['studio'];s.name_edit.setText('命名核心')
        s.verify_current();self.assertTrue(s.publish_btn.isEnabled())
        asset=s.publish_current();self.assertIsNotNone(asset)
        ident=asset['id']
        s.bench_controls['source'].setPlainText('ADDI x1,x0,77\nHALT')
        self.assertTrue(s.publish_btn.isEnabled())
        s.run_bench();self.assertEqual(s.last_result['registers'][1],77)
        s.bench_controls['source'].setPlainText('ADDI x1,x0,88\nHALT')
        self.assertEqual(s.output_tabs.count(),0)
        self.assertTrue(s.publish_btn.isEnabled())
        self.assertEqual(s.publish_current()['id'],ident)
        s.controls['alu_ports'].setValue(3)
        self.assertFalse(s.publish_btn.isEnabled())
        self.assertIsNone(s.current.get('published_id'))

    def test_publish_cor_import_and_instance_into_soc(self):
        w=self.window;s=w.screens['studio'];s.new_design('npu');s.verify_current()
        asset=s.publish_current();self.assertIsNotNone(asset)
        with tempfile.TemporaryDirectory() as td:
            path=write_asset(Path(td)/'design.cor',asset)
            imported=s.import_path(path)
            self.assertEqual(imported['design'],read_asset(path)['design'])
            self.assertEqual(s.current['hardware'],asset['design']['hardware'])
        w.start_scenario('sandbox');s.instantiate(asset)
        self.assertEqual(w.design.ip_blocks['npu'],asset['id'])
        self.assertTrue(any(asset['name'] in block.label for block in w.result['plan'].blocks))

    def test_modes_and_graph_selection_do_not_change_design(self):
        w=self.window;s=w.screens['studio'];hardware=dict(s.current['hardware'])
        for mode in ('beginner','intermediate','advanced','professional'):
            w.mode_picker.setCurrentIndex(w.mode_picker.findData(mode))
            self.assertEqual(s.current['hardware'],hardware)
        s.graph.module_selected.emit('cache')
        self.assertEqual(s.selected_module,'cache')

    def test_invalid_hardware_can_be_saved_as_draft_but_not_published(self):
        s=self.window.screens['studio']
        s.controls['hit_latency'].setValue(100)
        s.controls['miss_latency'].setValue(2)
        s.verify_current();self.assertFalse(s.publish_btn.isEnabled())
        self.assertIn('hit_latency',s.status.text())
        again=MainWindow();self.addCleanup(again.close)
        self.assertEqual(again.screens['studio'].current['hardware']['hit_latency'],100)

    def test_soc_architecture_displays_custom_accelerator_and_can_replace_it(self):
        w=self.window;s=w.screens['studio'];s.new_design('gpu');s.name_edit.setText('我的GPU')
        s.verify_current();asset=s.publish_current();w.start_scenario('sandbox');s.instantiate(asset)
        architecture=w.screens['architecture']
        self.assertEqual(architecture.gpu.currentData(),'ip:'+asset['id'])
        self.assertIn('我的GPU',architecture.gpu_info.text())
        architecture.gpu.setCurrentIndex(architecture.gpu.findData('g925'))
        w.recompute_now()
        self.assertNotIn('gpu',w.design.ip_blocks)
        self.assertEqual(w.result['plan'].metrics['gpu']['id'],'g925')

    def test_imported_template_names_remain_visible_without_local_catalog(self):
        design=empty_design('sandbox');record=export.payload(design,None)
        w=self.window
        with tempfile.TemporaryDirectory() as td:
            import json
            path=Path(td)/'standalone.sil';path.write_text(json.dumps(record))
            with patch.dict(CORES,{},clear=True),patch.dict(GPUS,{},clear=True),patch.dict(NPUS,{},clear=True):
                w.import_soc(str(path))
                architecture=w.screens['architecture']
                self.assertEqual(architecture.rows[0]['combo'].currentData(),'x925')
                self.assertIn('Cortex-X925',architecture.rows[0]['combo'].currentText())
                self.assertEqual(architecture.gpu.currentData(),'g925')
                self.assertIn('G925',architecture.gpu.currentText())

    def test_sil_embedded_core_can_be_edited_without_separate_cor(self):
        design=empty_design('sandbox');asset=make_design_asset('isp','文件内的ISP',default_hardware('isp'))
        attach_asset(design,asset)
        with tempfile.TemporaryDirectory() as td:
            path=export.export_to(Path(td)/'complete.sil',design,None)
            w=self.window;w.import_soc(str(path));s=w.screens['studio']
            self.assertEqual(w.ip_library,{})
            s.refresh()
            item=next(s.library_list.item(i) for i in range(s.library_list.count()) if '文件内的ISP' in s.library_list.item(i).text())
            s.library_list.setCurrentItem(item);s.load_selected()
            self.assertEqual(s.current['hardware'],asset['design']['hardware'])
            self.assertEqual(s._current_asset()['id'],asset['id'])
            self.assertTrue(s.export_btn.isEnabled())

    def test_cpu_performance_updates_from_hardware_and_can_compare_baseline(self):
        s=self.window.screens['studio']
        s.controls['width'].setValue(1);s.controls['execution_ports'].setValue(1);s.controls['alu_ports'].setValue(1)
        s.run_performance();first=s.last_performance['ipc'];s._pin_performance()
        s.controls['width'].setValue(4);s.controls['execution_ports'].setValue(4);s.controls['alu_ports'].setValue(4)
        s.run_performance();self.assertGreater(s.last_performance['ipc'],first)
        self.assertEqual(s.last_performance['hardware']['alu_ports'],4)
        self.assertIn('IPC对照变化',[s.output_tabs.widget(0).horizontalHeaderItem(i).text() for i in range(s.output_tabs.widget(0).columnCount())])

    def test_x86_template_can_be_added_and_opened_in_lab_with_opaque_menu(self):
        w=self.window;w.start_scenario('x86_workstation');screen=w.screens['architecture'];screen.refresh()
        menu=screen._make_add_menu('x86');self.addCleanup(menu.close)
        self.assertTrue(any('双发射' in a.text() for a in menu.actions()))
        menu.resize(menu.sizeHint());menu.show();self.app.processEvents()
        pixel=menu.grab().toImage().pixelColor(3,3)
        self.assertEqual(pixel.alpha(),255)
        self.assertLess(pixel.red(),90)
        screen._show_core_info(0);screen._edit_template()
        self.assertEqual(w.screens['studio'].current['hardware']['architecture'],'x86_32')
        self.assertEqual(w.screens['studio'].current['hardware']['width'],2)


if __name__=='__main__':unittest.main()
