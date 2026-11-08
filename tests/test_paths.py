import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from silicon_professor.paths import resource_root,player_data_dir


class TestPaths(unittest.TestCase):
    def test_frozen_resources_and_writable_save_are_separate(self):
        with patch.dict('os.environ',{},clear=True),patch('sys.frozen',True,create=True),patch('sys._MEIPASS','/bundle/resources',create=True):
            self.assertEqual(resource_root(),Path('/bundle/resources'))
            with patch('sys.platform','win32'),patch.dict('os.environ',{'LOCALAPPDATA':'C:/Users/player/AppData/Local'}):
                self.assertEqual(player_data_dir(),Path('C:/Users/player/AppData/Local/SiliconImmortal'))
            with patch('sys.platform','darwin'),patch('pathlib.Path.home',return_value=Path('/Users/player')):
                self.assertEqual(player_data_dir(),Path('/Users/player/Library/Application Support/SiliconImmortal'))

    def test_explicit_save_directory_and_source_legacy_saves(self):
        with tempfile.TemporaryDirectory() as td,patch.dict('os.environ',{'SILICON_PROFESSOR_SAVE_DIR':td}):
            self.assertEqual(player_data_dir(),Path(td))
