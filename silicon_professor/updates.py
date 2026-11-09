"""镜像优先的源码发布检查与下载；联网工作由界面后台线程调用。"""
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import shutil
import socket
from urllib.parse import urlsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler
import uuid

from .update_package import MAX_ARCHIVE,MANIFEST,version_key,source_version,stage_archive

FORGEJO='https://code.qiisme1021.space'
GITHUB='https://github.com/qi-1021/silicon-immortal'
RAW='https://raw.githubusercontent.com/qi-1021/silicon-immortal/main/silicon_professor/version.py'
DEFAULT_MIRRORS=['https://ghfast.top/']
ZIP_NAME='SiliconImmortal-source.zip'
SHA_NAME='SHA256SUMS.txt'


def _https(url):
    if not isinstance(url,str) or len(url)>2048:raise ValueError('更新地址无效。')
    p=urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443) or p.fragment:
        raise ValueError('更新地址必须是无认证信息的HTTPS地址。')
    host=p.hostname.lower()
    if host=='localhost' or host.endswith('.local'):raise ValueError('更新地址不能指向本机。')
    try:
        if not ipaddress.ip_address(host).is_global:raise ValueError('更新地址不能指向私有地址。')
    except ValueError as ex:
        if '不能' in str(ex):raise
    return p


def normalize_mirrors(values):
    if not isinstance(values,list) or len(values)>4:raise ValueError('最多配置四个GitHub代理镜像。')
    out=[]
    for value in values:
        p=_https(value)
        if p.query or '/https:' in p.path:raise ValueError('填写镜像前缀，不要包含上游URL或查询参数。')
        value=value.rstrip('/')+'/'
        if value not in out:out.append(value)
    return out


class SecureRedirect(HTTPRedirectHandler):
    def __init__(self,hosts):self.hosts=hosts;super().__init__()

    def redirect_request(self,req,fp,code,msg,headers,newurl):
        parsed=_https(newurl)
        if parsed.hostname not in self.hosts:raise ValueError('更新下载重定向到了未授权来源。')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def fetch_bytes(url,limit,progress=None):
    parsed=_https(url)
    # Resolve before requesting; update sources cannot access private/local network endpoints.
    for address in socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(address[4][0]).is_global:raise ValueError('更新来源解析到私有地址。')
    allowed={parsed.hostname,'github.com','raw.githubusercontent.com','release-assets.githubusercontent.com','objects.githubusercontent.com'}
    opener=build_opener(SecureRedirect(allowed))
    request=Request(url,headers={'User-Agent':'SiliconImmortal-source-updater','Accept':'application/json,application/octet-stream,*/*'})
    with opener.open(request,timeout=10) as response:
        length=response.headers.get('Content-Length');total=int(length) if length and length.isdigit() else 0
        if total>limit:raise ValueError('更新响应超过大小上限。')
        chunks=[];size=0
        while True:
            data=response.read(min(65536,limit-size+1))
            if not data:break
            chunks.append(data);size+=len(data)
            if size>limit:raise ValueError('更新响应超过大小上限。')
            if progress:progress(size,total)
        return b''.join(chunks)


def _sources(mirrors):
    return [('forgejo',FORGEJO)]+[('proxy',m) for m in normalize_mirrors(DEFAULT_MIRRORS if mirrors is None else mirrors)]+[('github','https://api.github.com')]


def _asset_url(kind,url):
    p=_https(url)
    if kind=='forgejo':
        if p.hostname!=urlsplit(FORGEJO).hostname or not (p.path.startswith('/attachments/') or p.path.startswith('/isqi/silicon-immortal/')):
            raise ValueError('镜像附件不属于本项目。')
    elif not url.startswith(GITHUB+'/releases/download/'):raise ValueError('GitHub附件不属于本项目。')
    return url


def release_at(kind,base,fetch,tag=None):
    if kind=='proxy':
        if tag is None:version=source_version(fetch(base+RAW,100000))
        else:version=tag.removeprefix('v');version_key(version)
        tag='v'+version
        return dict(source=kind,base=base,version=version,tag=tag,notes='',
                    zip=base+GITHUB+'/releases/download/'+tag+'/'+ZIP_NAME,
                    checksum=base+GITHUB+'/releases/download/'+tag+'/'+SHA_NAME)
    api=(FORGEJO+'/api/v1/repos/isqi/silicon-immortal/releases?limit=20' if kind=='forgejo'
         else 'https://api.github.com/repos/qi-1021/silicon-immortal/releases?per_page=20')
    if tag:
        api=(FORGEJO+'/api/v1/repos/isqi/silicon-immortal/releases/tags/' if kind=='forgejo' else 'https://api.github.com/repos/qi-1021/silicon-immortal/releases/tags/')+tag
    raw=json.loads(fetch(api,2_000_000));releases=[raw] if tag else raw
    if not isinstance(releases,list):raise ValueError('发布接口没有返回列表。')
    candidates=[]
    for record in releases[:20]:
        if not isinstance(record,dict) or record.get('draft'):continue
        try:key=version_key(record.get('tag_name'))
        except ValueError:continue
        candidates.append((key,record))
    if not candidates:raise ValueError('发布源没有可识别的版本。')
    record=max(candidates,key=lambda v:v[0])[1];release_tag=record['tag_name']
    if not release_tag.startswith('v'):raise ValueError('发布标签不是v版本标签。')
    assets=record.get('assets',[])
    if not isinstance(assets,list):raise ValueError('发布附件格式无效。')
    by_name={a.get('name'):a for a in assets if isinstance(a,dict)}
    if not {ZIP_NAME,SHA_NAME}<=set(by_name):raise ValueError('最新发布尚无源码ZIP或校验清单。')
    return dict(source=kind,base=base,version=release_tag[1:],tag=release_tag,
        notes=str(record.get('body') or '')[:8000],
        zip=_asset_url(kind,by_name[ZIP_NAME].get('browser_download_url')),
        checksum=_asset_url(kind,by_name[SHA_NAME].get('browser_download_url')))


def check_updates(current,mirrors=None,fetch=fetch_bytes,notify=None):
    current_key=version_key(current);best=None;errors=[]
    for kind,base in _sources(mirrors):
        if notify:notify('检查 '+base)
        try:
            release=release_at(kind,base,fetch)
            # A raw main version is not a release until its tagged checksum is available.
            if kind=='proxy':checksum_for(fetch(release['checksum'],100000))
            if best is None or version_key(release['version'])>version_key(best['version']):best=release
            if version_key(release['version'])>current_key:
                return dict(available=True,release=release,errors=errors)
        except (OSError,ValueError,TypeError,KeyError) as ex:errors.append(f'{base} · {type(ex).__name__}')
    if best:return dict(available=False,release=best,errors=errors)
    raise ValueError('全部更新源暂不可用；当前版本未改动。\n'+'\n'.join(errors))


def checksum_for(data):
    try:text=data.decode('utf-8')
    except UnicodeError as ex:raise ValueError('摘要清单不是UTF-8。') from ex
    found=[]
    for line in text.splitlines():
        pair=line.split()
        if len(pair)==2 and pair[1].lstrip('*')==ZIP_NAME and re.fullmatch('[0-9a-fA-F]{64}',pair[0]):found.append(pair[0].lower())
    if len(found)!=1:raise ValueError('摘要清单没有唯一源码ZIP的SHA-256。')
    return found[0]


def download_update(release,cache,mirrors=None,fetch=fetch_bytes,notify=None,progress=None):
    version_key(release['version']);errors=[];sources=_sources(mirrors);expected_digest=None
    first=(release['source'],release['base'])
    if first in sources:sources.remove(first)
    sources.insert(0,first)
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    for kind,base in sources:
        if notify:notify('下载 '+base)
        folder=None
        try:
            candidate=release if (kind,base)==first else release_at(kind,base,fetch,tag=release['tag'])
            if candidate['tag']!=release['tag']:raise ValueError('备用来源的发布标签不一致。')
            digest=checksum_for(fetch(candidate['checksum'],100000))
            if expected_digest is not None and digest!=expected_digest:raise ValueError('同一版本在不同来源的SHA-256不一致。')
            expected_digest=digest
            data=fetch(candidate['zip'],MAX_ARCHIVE,progress)
            folder=cache/uuid.uuid4().hex;folder.mkdir()
            manifest=stage_archive(data,digest,release['version'],folder/'stage')
            # The running installer is the current trusted helper, not one taken from the download.
            shutil.copy2(Path(__file__).with_name('update_package.py'),folder/'installer.py')
            return dict(stage=folder/'stage',version=manifest['version'],sha256=digest,source=base,installer=folder/'installer.py')
        except (OSError,ValueError,TypeError,KeyError) as ex:
            if folder and folder.exists():shutil.rmtree(folder)
            errors.append(f'{base} · {type(ex).__name__}')
    raise ValueError('下载或校验失败；当前版本未改动。\n'+'\n'.join(errors))
