"""各平台共享测试入口，不读写玩家数据。"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='silicon-tests-') as temp:
    env=dict(os.environ,QT_QPA_PLATFORM='offscreen',SILICON_PROFESSOR_SAVE_DIR=temp)
    raise SystemExit(subprocess.call([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,env=env))
