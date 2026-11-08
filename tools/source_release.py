"""发布带离线手册的源码ZIP；运行时由平台启动脚本安装，不打包程序。"""
from pathlib import Path
import io
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    output=ROOT/'release-assets';output.mkdir(exist_ok=True)
    archive=subprocess.check_output(['git','archive','--format=zip','--prefix=SiliconImmortal/','HEAD'],cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archive)) as source,zipfile.ZipFile(output/'SiliconImmortal-source.zip','w',zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():target.writestr(item,source.read(item.filename))
        manual=ROOT/'docs/player-guide/index.html'
        if not manual.is_file():raise ValueError('先运行tools/build_manual.py生成离线手册。')
        target.write(manual,'SiliconImmortal/docs/player-guide/index.html')
    print(output/'SiliconImmortal-source.zip')

if __name__=='__main__':main()
