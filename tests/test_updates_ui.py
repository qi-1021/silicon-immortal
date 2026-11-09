import os
import tempfile
import unittest
import threading
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QCloseEvent
from silicon_professor import save
from silicon_professor.ui.main_window import MainWindow


class TestUpdatesUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup)
        p=patch.multiple(save,SAVE_DIR=Path(td.name),SAVE_PATH=Path(td.name)/'save.json')
        p.start();self.addCleanup(p.stop)
        self.win=MainWindow();self.addCleanup(self.win.close)

    def test_entry_needs_no_project_and_mirror_configuration_restores(self):
        w=self.win;w.update_button.click();s=w.screens['updates']
        self.assertIs(w.stack.currentWidget(),s);self.assertIsNone(w.design)
        s.mirrors.setPlainText('https://mirror.example/\nhttps://second.example/')
        s.save_settings()
        again=MainWindow();self.addCleanup(again.close)
        self.assertIn('https://second.example/',again.screens['updates'].mirrors.toPlainText())
        self.assertFalse(s.install_btn.isEnabled())

    def test_compact_sidebar_keeps_legible_buttons_with_scrolling(self):
        from PySide6.QtWidgets import QScrollArea,QPushButton
        w=self.win;w.resize(1180,760);w.show();self.app.processEvents()
        nav=w.findChild(QScrollArea,'NavigationScroll')
        self.assertIsNotNone(nav)
        self.assertGreater(nav.verticalScrollBar().maximum(),0)
        for button in nav.widget().findChildren(QPushButton):
            self.assertGreaterEqual(button.height(),34,button.text())

    def test_invalid_mirror_does_not_replace_settings_or_start_network(self):
        s=self.win.screens['updates'];original=dict(self.win.update_settings)
        s.mirrors.setPlainText('http://unsafe.example/');s.check()
        self.assertIsNone(s.worker)
        self.assertEqual(self.win.update_settings,original)
        self.assertIn('HTTPS',s.status.text())

    def test_checked_release_download_and_git_directory_install_guard(self):
        s=self.win.screens['updates']
        s._checked(dict(available=True,release=dict(version='0.1.0-alpha.6',base='https://mirror.example/',notes='notes'),errors=[]))
        self.assertTrue(s.download_btn.isEnabled())
        s._downloaded(dict(stage=Path('/tmp/staged-update'),version='0.1.0-alpha.6',sha256='a'*64,source='https://mirror.example/',installer=Path('/tmp/installer.py')))
        self.assertFalse(s.install_btn.isEnabled())
        self.assertIn('Git',s.status.text())

    def test_check_runs_in_background_and_error_keeps_application_open(self):
        s=self.win.screens['updates']
        with patch('silicon_professor.ui.updates.check_updates',side_effect=ValueError('所有来源不可用')):
            s.check();worker=s.worker
            self.assertIsNotNone(worker);worker.wait(3000)
            for _ in range(8):self.app.processEvents()
        self.assertIsNone(s.worker);self.assertTrue(s.check_btn.isEnabled())
        self.assertFalse(s.download_btn.isEnabled())
        self.assertIn('所有来源不可用',s.status.text())

    def test_window_close_waits_for_background_job_without_destroying_thread(self):
        s=self.win.screens['updates'];gate=threading.Event()
        def wait(*args,**kwargs):
            gate.wait(3);raise ValueError('stopped')
        with patch('silicon_professor.ui.updates.check_updates',side_effect=wait):
            s.check();worker=s.worker
            try:
                event=QCloseEvent();self.win.closeEvent(event)
                self.assertFalse(event.isAccepted())
                self.assertIn('更新任务',s.status.text())
            finally:
                gate.set();worker.wait(4000)
                for _ in range(8):self.app.processEvents()
        event=QCloseEvent();self.win.closeEvent(event);self.assertTrue(event.isAccepted())

    def test_install_runs_helper_after_user_confirmation_and_saves_before_exit(self):
        s=self.win.screens['updates']
        from PySide6.QtWidgets import QMessageBox
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'installed';root.mkdir();stage=Path(td)/'update/stage';stage.mkdir(parents=True)
            s.package=dict(stage=stage,version='0.1.0-alpha.6',installer=stage.parent/'installer.py')
            with patch('silicon_professor.ui.updates.resource_root',return_value=root),patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes),\
                 patch('silicon_professor.ui.updates.subprocess.Popen') as launch,patch.object(self.win,'persist') as persist,patch.object(self.win,'close') as close:
                s.install();self.assertTrue(persist.called);self.assertTrue(close.called)
                command=launch.call_args.args[0]
                self.assertIn('--wait-pid',command);self.assertIn(str(root),command)
