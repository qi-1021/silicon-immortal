"""真实PicoRV32 RTL的独立编译/自检入口；不把解析模型结果当RTL通过。"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile

from ..paths import resource_root
ROOT=resource_root()
BUNDLE=ROOT/'third_party/picorv32'


def rtl_info():return json.loads((BUNDLE/'manifest.json').read_text('utf-8'))


def test_picorv32():
    info=rtl_info()
    for name,expected in info['sha256'].items():
        if hashlib.sha256((BUNDLE/name).read_bytes()).hexdigest()!=expected:
            return dict(status='failed',reason='RTL bundle hash mismatch: '+name,revision=info['revision'])
    compiler=shutil.which('iverilog');runtime=shutil.which('vvp')
    if not compiler or not runtime:return dict(status='unavailable',reason='需要 Icarus Verilog 的 iverilog 与 vvp；未运行RTL，不能标通过。',revision=info['revision'])
    try:
        with tempfile.TemporaryDirectory(prefix='silicon-rtl-') as directory:
            executable=Path(directory)/'smoke.vvp'
            compile_result=subprocess.run([compiler,'-g2012','-s','tb_silicon','-o',str(executable),str(BUNDLE/'picorv32.v'),str(BUNDLE/'tb_silicon.v')],capture_output=True,text=True,timeout=30)
            if compile_result.returncode:return dict(status='failed',reason=compile_result.stderr[-5000:],revision=info['revision'])
            run_result=subprocess.run([runtime,str(executable)],capture_output=True,text=True,timeout=15)
            passed=run_result.returncode==0 and 'SILICON_RTL_PASS' in run_result.stdout
            return dict(status='passed' if passed else 'failed',reason=(run_result.stdout+run_result.stderr)[-5000:],revision=info['revision'],
                        scope='actual RTL smoke test: ADDI/ADDI/SW; not full ISA compliance or PDK signoff')
    except (OSError,subprocess.TimeoutExpired) as ex:return dict(status='failed',reason=str(ex),revision=info['revision'])
