"""实际调用平台源码脚本启动GUI与文件测试，使用独立玩家目录。"""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='silicon-source-launch-') as td:
        output=Path(td)/'source.json'
        env=os.environ|dict(PYTHONUTF8='1',QT_QPA_PLATFORM='offscreen',SILICON_PROFESSOR_SAVE_DIR=str(Path(td)/'player'))
        cmd=['cmd','/c',str(ROOT/'run.bat')] if os.name=='nt' else ['bash',str(ROOT/'run.command')]
        subprocess.run(cmd+['--smoke-test',str(output)],check=True,cwd=ROOT,env=env,timeout=180)
        report=json.loads(output.read_text(encoding='utf-8'))
        if not report.get('passed'):raise RuntimeError('源码脚本未确认成功启动。')
        print('Source launcher passed:',sys.platform,report['version'])

if __name__=='__main__':main()
