"""源码启动：可用Python创建本项目虚拟环境，错误直接退出。"""
from pathlib import Path
import os
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parents[1]


def main():
    if sys.version_info<(3,12):raise SystemExit('需要Python 3.12或更新版本，请安装后重新启动。')
    python=ROOT/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.is_file():
        print('首次启动：创建虚拟环境并安装PySide6，需要联网。',flush=True)
        venv.EnvBuilder(with_pip=True).create(ROOT/'.venv')
    check=subprocess.run([str(python),'-c','from importlib.metadata import version; assert version("PySide6")=="6.12.0"'],capture_output=True)
    if check.returncode:subprocess.run([str(python),'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True)
    return subprocess.call([str(python),'-m','silicon_professor',*sys.argv[1:]],cwd=ROOT)

if __name__=='__main__':raise SystemExit(main())
