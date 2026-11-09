"""源码更新包验证与可回滚安装。仅标准库，可复制到独立进程运行。"""
import ast
import hashlib
import io
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import stat
import sys
import time
import uuid
import zipfile

MANIFEST='update-manifest.json'
MAX_ARCHIVE=128*1024*1024
MAX_EXPANDED=512*1024*1024
TOP_FILES={'README.md','LICENSE','THIRD_PARTY_NOTICES.md','requirements.txt','requirements-docs.txt',
           'run.bat','run.sh','run.command','test.command'}
ROOTS={'silicon_professor','docs','tools','tests','assets','third_party'}
RESERVED={'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}
PRIVATE={'docs/WORKLOG.md','docs/CODEX_CONTEXT.md','docs/CODEX_HANDOFF.md'}
JOURNAL='.silicon-update-journal.json'
LOCK='.silicon-update-lock'
BACKUPS='.silicon-update-backups'


def version_key(value):
    if not isinstance(value,str):raise ValueError('版本不是字符串。')
    match=re.fullmatch(r'v?(\d{1,3})\.(\d{1,3})\.(\d{1,3})(?:-(alpha|beta|rc)\.(\d{1,4}))?',value)
    if not match:raise ValueError('更新版本格式无效。')
    major,minor,patch,channel,serial=match.groups()
    return (int(major),int(minor),int(patch),{'alpha':0,'beta':1,'rc':2,None:3}[channel],int(serial or 0))


def managed_path(name):
    if not isinstance(name,str) or not name or '\\' in name or ':' in name:return False
    path=PurePosixPath(name)
    if path.is_absolute() or str(path)!=name or any(p in ('','..','.') or p.startswith('.') for p in path.parts):return False
    if any(p.endswith((' ','.')) or p.split('.',1)[0].upper() in RESERVED or any(ord(c)<32 or c in '<>"|?*' for c in p) for p in path.parts):return False
    if name in PRIVATE or name.startswith('docs/superpowers/') or '__pycache__' in path.parts or name.endswith('.pyc'):return False
    return name in TOP_FILES or len(path.parts)>1 and path.parts[0] in ROOTS


def build_manifest(version,files):
    version_key(version)
    if not isinstance(files,dict) or not files or len(files)>5000 or any(not managed_path(name) for name in files):
        raise ValueError('包内程序文件路径无效。')
    return dict(format='silicon-source-update',schema=1,version=version.removeprefix('v'),
        python_min=[3,12],files={name:hashlib.sha256(data).hexdigest() for name,data in files.items()})


def validate_manifest(record,expected=None):
    if not isinstance(record,dict) or record.get('format')!='silicon-source-update' or type(record.get('schema')) is not int or record['schema']!=1:
        raise ValueError('没有兼容的源码更新清单；可下载后手动解压。')
    version_key(record.get('version'))
    if expected and record['version']!=expected.removeprefix('v'):raise ValueError('更新包版本与所选发布不一致。')
    minimum=record.get('python_min')
    if not isinstance(minimum,list) or len(minimum)!=2 or any(type(v) is not int or not 0<=v<=99 for v in minimum) or tuple(minimum)>sys.version_info[:2]:
        raise ValueError('本机Python版本不满足更新包要求。')
    files=record.get('files')
    if not isinstance(files,dict) or not files or len(files)>5000:raise ValueError('更新文件清单无效。')
    seen=set()
    for name,digest in files.items():
        if not managed_path(name) or name.casefold() in seen or not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest):
            raise ValueError('更新清单包含不安全路径或无效摘要。')
        seen.add(name.casefold())
    required={'silicon_professor/version.py','silicon_professor/__init__.py','silicon_professor/__main__.py','tools/bootstrap.py','requirements.txt'}
    if not required<=set(files):raise ValueError('更新缺少必需的程序/启动文件。')
    return record


def source_version(data):
    if len(data)>100000:raise ValueError('版本文件太大。')
    try:tree=ast.parse(data.decode('utf-8'))
    except (ValueError,SyntaxError,UnicodeError) as ex:raise ValueError('版本文件无效。') from ex
    values=[node.value.value for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GAME_VERSION' for t in node.targets)
            and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str)]
    if len(values)!=1:raise ValueError('版本文件没有唯一GAME_VERSION常量。')
    version_key(values[0]);return values[0]


def stage_archive(data,digest,version,target):
    if len(data)>MAX_ARCHIVE or hashlib.sha256(data).hexdigest()!=digest:raise ValueError('源码ZIP的SHA-256不一致或超过上限。')
    target=Path(target)
    if target.exists():raise ValueError('更新暂存目录已存在。')
    files={};modes={};total=0;manifest_data=None;seen=set()
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if len(z.infolist())>6000:raise ValueError('ZIP条目过多。')
            for item in z.infolist():
                name=item.filename
                if not name.startswith('SiliconImmortal/') or '\\' in name:raise ValueError('ZIP根路径无效。')
                rel=name[len('SiliconImmortal/'):]
                mode=item.external_attr>>16
                if stat.S_ISLNK(mode) or mode&0o170000 not in (0,0o100000,0o040000):raise ValueError('ZIP不允许链接或特殊文件。')
                if item.is_dir():
                    if rel and not managed_path(rel.rstrip('/')+'/placeholder'):raise ValueError('ZIP目录路径无效。')
                    continue
                if rel!=MANIFEST and not managed_path(rel):raise ValueError('ZIP包含不允许的程序路径。')
                if rel.casefold() in seen:raise ValueError('ZIP包含重复路径。')
                seen.add(rel.casefold());total+=item.file_size
                if item.file_size>32*1024*1024 or total>MAX_EXPANDED or item.flag_bits&1:raise ValueError('ZIP体积过大或已加密。')
                if item.file_size>max(1,item.compress_size)*500:raise ValueError('ZIP压缩比异常。')
                content=z.read(item)
                if rel==MANIFEST:manifest_data=content
                else:files[rel]=content;modes[rel]=0o755 if mode&0o111 else 0o644
    except (zipfile.BadZipFile,RuntimeError) as ex:raise ValueError('无法解码源码ZIP。') from ex
    if not manifest_data or len(manifest_data)>1_000_000:raise ValueError('缺少逐文件更新清单；旧发布请手动安装。')
    try:manifest=validate_manifest(json.loads(manifest_data),version)
    except (ValueError,UnicodeError) as ex:raise ValueError('更新清单无效：'+str(ex)) from ex
    if set(files)!=set(manifest['files']):raise ValueError('ZIP文件与清单不匹配。')
    if source_version(files['silicon_professor/version.py'])!=manifest['version']:raise ValueError('源码版本与更新清单不同。')
    for name,content in files.items():
        if hashlib.sha256(content).hexdigest()!=manifest['files'][name]:raise ValueError('更新文件摘要不匹配。')
        if name.endswith('.py'):
            try:compile(content,name,'exec')
            except (SyntaxError,ValueError) as ex:raise ValueError('更新Python文件语法无效：'+name) from ex
    target.mkdir(parents=True)
    try:
        for name,content in files.items():
            path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content);path.chmod(modes[name])
        (target/MANIFEST).write_bytes(manifest_data)
    except BaseException:
        shutil.rmtree(target);raise
    return manifest


def _safe_target(root,rel):
    if rel!=MANIFEST and not managed_path(rel):raise ValueError('安装路径无效。')
    path=root/rel
    if root.is_symlink() or any(p.is_symlink() for p in [path,*path.parents] if p==root or root in p.parents):
        raise ValueError('安装目标包含符号链接。')
    if path.exists() and not path.is_file():raise ValueError('程序路径与目录冲突。')
    return path


def _atomic_copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_name('.'+target.name+'.update-'+uuid.uuid4().hex)
    try:
        shutil.copy2(source,tmp)
        with tmp.open('rb') as file:os.fsync(file.fileno())
        os.replace(tmp,target);_sync_directory(target.parent)
    finally:
        if tmp.exists():tmp.unlink()


def _sync_directory(path):
    if os.name=='nt':return
    fd=os.open(path,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def _atomic_json(target,record):
    tmp=target.with_name('.'+target.name+'.update-'+uuid.uuid4().hex)
    try:
        with tmp.open('w',encoding='utf-8') as file:
            json.dump(record,file);file.flush();os.fsync(file.fileno())
        os.replace(tmp,target);_sync_directory(target.parent)
    finally:
        if tmp.exists():tmp.unlink()


def _alive(pid):
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=(wintypes.DWORD,wintypes.BOOL,wintypes.DWORD)
        kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes=(wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD))
        kernel.GetExitCodeProcess.restype=wintypes.BOOL
        kernel.CloseHandle.argtypes=(wintypes.HANDLE,)
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:return ctypes.get_last_error()==5
        try:
            code=wintypes.DWORD()
            return bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
        finally:kernel.CloseHandle(handle)
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False
    except PermissionError:return True


def recover_update(root):
    root=Path(root);journal=root/JOURNAL;lock=root/LOCK
    if not journal.exists():return False
    if journal.is_symlink() or journal.stat().st_size>1_000_000:raise ValueError('更新恢复记录无效。')
    record=json.loads(journal.read_text());pid=record.get('pid')
    if type(pid) is not int or pid<=0:raise ValueError('恢复进程记录无效。')
    if pid!=os.getpid() and _alive(pid):raise ValueError('更新安装仍在运行，请稍后启动。')
    ident=record.get('backup')
    if not isinstance(ident,str) or not re.fullmatch('[0-9a-f]{32}',ident):raise ValueError('更新备份记录无效。')
    backup=root/BACKUPS/ident
    if backup.is_symlink() or (root/BACKUPS).is_symlink():raise ValueError('备份目录包含链接。')
    operations=record.get('operations')
    if not isinstance(operations,list) or len(operations)>6000:raise ValueError('恢复操作数无效。')
    for op in reversed(operations):
        if not isinstance(op,dict) or type(op.get('existed')) is not bool:raise ValueError('恢复操作无效。')
        target=_safe_target(root,op.get('path'));saved=backup/op['path']
        if op['existed']:
            if not saved.is_file() or saved.is_symlink():raise ValueError('更新备份缺失，保留现场。')
            _atomic_copy(saved,target)
        elif target.exists():target.unlink()
    journal.unlink()
    if lock.is_dir():lock.rmdir()
    return True


def apply_update(root,stage):
    root=Path(root).absolute();stage=Path(stage).absolute()
    if root.is_symlink() or (root/'.git').exists():raise ValueError('Git开发目录不自动覆盖；请下载源码另行安装。')
    if not root.is_dir() or not stage.is_dir() or stage.is_symlink():raise ValueError('更新目录无效。')
    if (root/JOURNAL).exists():recover_update(root)
    manifest=validate_manifest(json.loads((stage/MANIFEST).read_text()))
    for rel,digest in manifest['files'].items():
        path=_safe_target(stage,rel)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('暂存文件被修改，拒绝安装。')
    if source_version((stage/'silicon_professor/version.py').read_bytes())!=manifest['version']:raise ValueError('暂存版本不一致。')
    old={}
    if (root/MANIFEST).exists():
        old=validate_manifest(json.loads(_safe_target(root,MANIFEST).read_text()))['files']
        for rel,digest in old.items():
            path=_safe_target(root,rel)
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                raise ValueError('本地程序文件有改动，保留当前版本：'+rel)
    rels=sorted(set(old)|set(manifest['files']))+[MANIFEST]
    for rel in rels:_safe_target(root,rel)
    if (root/BACKUPS).is_symlink() or (root/LOCK).is_symlink():raise ValueError('更新工作目录包含链接。')
    lock=root/LOCK
    try:lock.mkdir()
    except FileExistsError as ex:raise ValueError('更新锁已存在，保留现场。') from ex
    ident=uuid.uuid4().hex;backup=root/BACKUPS/ident;operations=[]
    try:
        backup.mkdir(parents=True)
        _atomic_copy(Path(__file__),backup/'recovery.py')
        for rel in rels:
            path=root/rel;existed=path.is_file();operations.append(dict(path=rel,existed=existed))
            if existed:
                saved=backup/rel;_atomic_copy(path,saved)
        # Journal is persisted before any live file is changed. Each replacement is atomic.
        _atomic_json(root/JOURNAL,dict(pid=os.getpid(),backup=ident,operations=operations))
        for rel in rels:
            target=root/rel
            if rel in manifest['files'] or rel==MANIFEST:_atomic_copy(stage/rel,target)
            elif target.exists():target.unlink()
        (root/JOURNAL).unlink();_sync_directory(root);lock.rmdir()
    except BaseException:
        if (root/JOURNAL).exists():recover_update(root)
        elif lock.exists():lock.rmdir()
        raise
    return dict(version=manifest['version'],backup=backup)


def main():
    import argparse
    import subprocess
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--stage');parser.add_argument('--wait-pid',type=int);parser.add_argument('--recover',action='store_true')
    args=parser.parse_args();root=Path(args.root)
    if args.recover:recover_update(root);return
    if not args.stage:raise ValueError('未指定更新暂存目录。')
    stage=Path(args.stage);log=stage.parent/'install-result.json'
    try:
        if args.wait_pid:
            deadline=time.monotonic()+120
            while _alive(args.wait_pid):
                if time.monotonic()>deadline:raise ValueError('游戏未退出，未执行更新。')
                time.sleep(.25)
        result=apply_update(root,stage)
        log.write_text(json.dumps(dict(ok=True,version=result['version'],backup=str(result['backup']))))
        subprocess.Popen([sys.executable,str(root/'tools/bootstrap.py')],cwd=root,start_new_session=True)
    except Exception as ex:
        log.write_text(json.dumps(dict(ok=False,error=str(ex))))
        raise


if __name__=='__main__':main()
