"""在当前操作系统原生打包；只构建当前CPU架构，不伪装跨编译结果。"""
from pathlib import Path
from importlib.metadata import distribution
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from silicon_professor.version import GAME_VERSION,MODEL_VERSION


def copy_licenses(destination):
    destination.mkdir(parents=True,exist_ok=True)
    for package in ('PySide6','PySide6_Essentials','PySide6_Addons','shiboken6','PyInstaller'):
        dist=distribution(package)
        for file in dist.files or []:
            if any(word in str(file).lower() for word in ('license','copying','copyright')):
                source=Path(dist.locate_file(file))
                if source.is_file():
                    target=destination/package/str(file)
                    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    import sysconfig
    python_license=Path(sysconfig.get_path('stdlib'))/'LICENSE.txt'
    if python_license.is_file():shutil.copy2(python_license,destination/'PYTHON_LICENSE.txt')
    else:
        # 运行时发行保留PSF许可全文，不以一个链接代替许可。
        candidates=[Path(sys.base_prefix)/'LICENSE.txt',Path(sys.base_prefix)/'Resources/LICENSE.txt']
        found=next((p for p in candidates if p.is_file()),None)
        if found:shutil.copy2(found,destination/'PYTHON_LICENSE.txt')


def main():
    if platform.system() not in ('Windows','Darwin'):raise SystemExit('本发行脚本当前只构建Windows/macOS。')
    subprocess.run([sys.executable,str(ROOT/'tools/build_manual.py')],check=True,cwd=ROOT)
    os_name='Windows' if os.name=='nt' else 'macOS'
    arch='arm64' if platform.machine().lower() in ('arm64','aarch64') else 'x64'
    name=f'SiliconImmortal-{GAME_VERSION}-{os_name}-{arch}'
    stage=ROOT/'build/release-stage'/name
    if stage.exists():shutil.rmtree(stage)
    stage.mkdir(parents=True)
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed','--name','SiliconImmortal',
        '--paths',str(ROOT),'--distpath',str(ROOT/'build/native-dist'),'--workpath',str(ROOT/'build/pyinstaller'),
        '--specpath',str(ROOT/'build'),'--collect-data','silicon_professor',
        '--add-data',str(ROOT/'assets')+os.pathsep+'assets',
        '--add-data',str(ROOT/'docs/player-guide')+os.pathsep+'docs/player-guide',
        '--add-data',str(ROOT/'docs/screens')+os.pathsep+'docs/screens',
        '--add-data',str(ROOT/'docs/examples')+os.pathsep+'docs/examples',
        '--add-data',str(ROOT/'docs/guide')+os.pathsep+'docs/guide',
        '--add-data',str(ROOT/'silicon_professor/data/evidence.json')+os.pathsep+'silicon_professor/data',
        '--add-data',str(ROOT/'third_party/picorv32')+os.pathsep+'third_party/picorv32']
    if os_name=='Windows':command+=['--icon',str(ROOT/'assets/app.ico')]
    else:command+=['--icon',str(ROOT/'assets/app.icns'),'--osx-bundle-identifier','space.qiisme1021.siliconimmortal']
    command.append(str(ROOT/'tools/launch.py'))
    subprocess.run(command,check=True,cwd=ROOT)
    built=ROOT/'build/native-dist'/('SiliconImmortal' if os_name=='Windows' else 'SiliconImmortal.app')
    target=stage/built.name;shutil.copytree(built,target,symlinks=True)
    executable=target/'SiliconImmortal.exe' if os_name=='Windows' else target/'Contents/MacOS/SiliconImmortal'
    with tempfile.TemporaryDirectory(prefix='silicon-package-smoke-') as temp:
        report=Path(temp)/'smoke.json'
        env=dict(os.environ,SILICON_PROFESSOR_SAVE_DIR=str(Path(temp)/'player'),QT_QPA_PLATFORM='offscreen')
        subprocess.run([str(executable),'--smoke-test',str(report)],check=True,timeout=120,env=env,cwd=temp)
        if not report.is_file() or not json.loads(report.read_text())['passed']:raise RuntimeError('打包GUI冒烟没有成功记录。')
        # 此处只在临时目录生成数据，证明包在工作目录之外运行。
        shutil.copy2(report,stage/'BUILD_SMOKE.json');shutil.copy2(report.with_suffix('.png'),stage/'BUILD_SMOKE.png')
    shutil.copytree(ROOT/'docs/player-guide',stage/'docs/player-guide')
    shutil.copytree(ROOT/'docs/screens',stage/'docs/screens')
    shutil.copytree(ROOT/'docs/examples',stage/'docs/examples')
    shutil.copytree(ROOT/'docs/guide',stage/'docs/guide')
    for file in ('FORMAT.md','MODEL.md','REFERENCES.md','LAB_MANUAL.md','CORE_STUDIO.md'):
        shutil.copy2(ROOT/'docs'/file,stage/'docs'/file)
    for file in ('LICENSE','THIRD_PARTY_NOTICES.md'):
        shutil.copy2(ROOT/file,stage/file)
    copy_licenses(stage/'licenses')
    shutil.copytree(ROOT/'third_party/qt',stage/'licenses/qt')
    shutil.copytree(ROOT/'third_party/picorv32',stage/'licenses/picorv32')
    (stage/'README_FIRST.txt').write_text(
        'Silicon Immortal / 硅仙人 '+GAME_VERSION+'\n\n'+
        ('双击 SiliconImmortal.exe 启动，不需要安装Python。\n' if os_name=='Windows' else '打开 SiliconImmortal.app 启动。支持macOS14+；首次打开请参考手册的未签名应用说明。\n')+
        '玩家手册：docs/player-guide/index.html（浏览器打开，可离线阅读）\n'+
        '例子：docs/examples；SoC导入.sil，LAB导入.cor。\n'+
        '本作是教学游戏，功能/资源/PPA为不同层次的模型，不能制造芯片。\n',encoding='utf-8')
    (stage/'VERSION.json').write_text(json.dumps(dict(version=GAME_VERSION,model=MODEL_VERSION,
        platform=os_name,architecture=arch,python=platform.python_version(),minimum_os='Windows 10 x64' if os_name=='Windows' else 'macOS 14'),indent=2),'utf-8')
    output=ROOT/'dist';output.mkdir(exist_ok=True)
    if os_name=='macOS':
        archive=output/(name+'.zip')
        # ditto保留.app符号链接、执行权限与Mac元数据。
        subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(stage),str(archive)],check=True)
    else:
        archive=Path(shutil.make_archive(str(output/name),'zip',stage.parent,stage.name))
    print(archive)

if __name__=='__main__':main()
