"""发布带离线手册的源码ZIP；运行时由平台启动脚本安装，不打包程序。"""
from pathlib import Path
import io
import subprocess
import zipfile
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from silicon_professor.update_package import MANIFEST,build_manifest,managed_path,source_version


def main():
    output=ROOT/'release-assets';output.mkdir(exist_ok=True)
    archive=subprocess.check_output(['git','archive','--format=zip','--prefix=SiliconImmortal/','HEAD'],cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archive)) as source,zipfile.ZipFile(output/'SiliconImmortal-source.zip','w',zipfile.ZIP_DEFLATED) as target:
        files={}
        for item in source.infolist():
            rel=item.filename.removeprefix('SiliconImmortal/')
            if item.is_dir() or not managed_path(rel):continue
            content=source.read(item.filename);files[rel]=content;target.writestr(item,content)
        manual=ROOT/'docs/player-guide/index.html'
        if not manual.is_file():raise ValueError('先运行tools/build_manual.py生成离线手册。')
        target.write(manual,'SiliconImmortal/docs/player-guide/index.html')
        files['docs/player-guide/index.html']=manual.read_bytes()
        version=source_version(files['silicon_professor/version.py'])
        target.writestr('SiliconImmortal/'+MANIFEST,json.dumps(build_manifest(version,files),ensure_ascii=False,indent=2))
    print(output/'SiliconImmortal-source.zip')

if __name__=='__main__':main()
