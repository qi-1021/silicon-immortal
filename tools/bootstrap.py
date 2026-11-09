"""源码启动：可用Python创建本项目虚拟环境，错误直接退出。"""
from pathlib import Path
import os
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parents[1]


def main():
    if sys.version_info<(3,12):raise SystemExit('需要Python 3.12或更新版本，请安装后重新启动。')
    journal=ROOT/'.silicon-update-journal.json'
    if journal.is_file():
        import json
        ident=json.loads(journal.read_text()).get('backup','')
        if not isinstance(ident,str) or len(ident)!=32 or any(c not in '0123456789abcdef' for c in ident):raise SystemExit('更新恢复记录无效，请保留目录。')
        recovery=ROOT/'.silicon-update-backups'/ident/'recovery.py'
        if not recovery.is_file() or recovery.is_symlink() or journal.is_symlink():raise SystemExit('更新恢复工具缺失或路径无效，请保留备份目录。')
        subprocess.run([sys.executable,str(recovery),'--root',str(ROOT),'--recover'],check=True)
    python=ROOT/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.is_file():
        print('首次启动：创建虚拟环境并安装PySide6，需要联网。',flush=True)
        venv.EnvBuilder(with_pip=True).create(ROOT/'.venv')
    check=subprocess.run([str(python),'-c','from importlib.metadata import version; assert version("PySide6")=="6.12.0"'],capture_output=True)
    if check.returncode:subprocess.run([str(python),'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True)
    return subprocess.call([str(python),'-m','silicon_professor',*sys.argv[1:]],cwd=ROOT)

if __name__=='__main__':raise SystemExit(main())
