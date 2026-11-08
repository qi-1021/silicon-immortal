import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from silicon_professor import save
from silicon_professor.ui.main_window import MainWindow


class TestChallengesUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_reference_solution_goals_and_progress_need_actual_tapeout(self):
        with tempfile.TemporaryDirectory() as td,patch.multiple(save,SAVE_DIR=Path(td),SAVE_PATH=Path(td)/'save.json'):
            win=MainWindow()
            try:
                sid='challenge_bandwidth';win.start_scenario(sid)
                brief=win.screens['brief'];brief.refresh()
                self.assertFalse(brief.challenge_card.isHidden())
                self.assertFalse(win.result['signoff']['ready'])
                brief._load_solution()
                self.assertTrue(win.result['signoff']['ready'])
                self.assertNotIn(sid,win.progress)
                win.tape_out()
                self.assertTrue(win.progress[sid]['challenge_completed'])
            finally:win.close()
