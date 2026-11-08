"""程序资源与玩家数据分开；冻结应用不向.app或_internal写存档。"""
from pathlib import Path
import os
import sys


def resource_root():
    return Path(sys._MEIPASS) if getattr(sys,'frozen',False) else Path(__file__).resolve().parent.parent


def player_data_dir():
    override=os.environ.get('SILICON_PROFESSOR_SAVE_DIR')
    if override:return Path(override).expanduser()
    if not getattr(sys,'frozen',False):return resource_root()/'saves'
    if sys.platform=='win32':return Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))/'SiliconImmortal'
    if sys.platform=='darwin':return Path.home()/'Library/Application Support/SiliconImmortal'
    return Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'SiliconImmortal'
