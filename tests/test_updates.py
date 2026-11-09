import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from silicon_professor.updates import (version_key,check_updates,download_update,normalize_mirrors)
from silicon_professor.update_package import (MANIFEST,build_manifest,stage_archive,apply_update,recover_update)


def archive(extra=None):
    files={'silicon_professor/version.py':b"GAME_VERSION='0.1.0-alpha.6'\n",
           'silicon_professor/__init__.py':b'', 'silicon_professor/__main__.py':b'',
           'tools/bootstrap.py':b'pass\n','run.sh':b'#!/bin/sh\n','requirements.txt':b'PySide6==6.12.0\n'}
    manifest=build_manifest('0.1.0-alpha.6',files)
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr('SiliconImmortal/'+name,data)
        z.writestr('SiliconImmortal/'+MANIFEST,json.dumps(manifest))
        for name,data in (extra or {}).items():z.writestr(name,data)
    return buffer.getvalue(),files


class TestUpdates(unittest.TestCase):
    def test_semantic_alpha_version_and_strict_https_proxy_setting(self):
        self.assertGreater(version_key('v0.1.0-alpha.10'),version_key('0.1.0-alpha.9'))
        self.assertGreater(version_key('0.1.0'),version_key('0.1.0-rc.8'))
        self.assertEqual(normalize_mirrors(['https://mirror.example/','https://mirror.example']),['https://mirror.example/'])
        for bad in ('http://mirror.example/','https://user:pass@mirror.example/','https://127.0.0.1/','https://mirror.example/?key=secret'):
            with self.assertRaises(ValueError):normalize_mirrors([bad])

    def test_manifest_rejects_cross_platform_reserved_names(self):
        for name in ('docs/CON.txt','tools/NUL.py','assets/icon.png.','assets/bad?.png'):
            with self.subTest(name=name),self.assertRaises(ValueError):build_manifest('0.1.0-alpha.6',{name:b'bad'})

    def test_github_blocked_forgejo_release_is_sufficient(self):
        def fetch(url,limit,progress=None):
            if 'code.qiisme' not in url:raise OSError('GitHub blocked')
            return json.dumps([dict(tag_name='v0.1.0-alpha.6',prerelease=True,draft=False,body='notes',
                assets=[dict(name='SiliconImmortal-source.zip',browser_download_url='https://code.qiisme1021.space/attachments/zip'),
                        dict(name='SHA256SUMS.txt',browser_download_url='https://code.qiisme1021.space/attachments/sha')])]).encode()
        r=check_updates('0.1.0-alpha.5',fetch=fetch)
        self.assertTrue(r['available']);self.assertEqual(r['release']['source'],'forgejo')

    def test_both_origins_blocked_proxy_raw_version_and_release_assets_work(self):
        data,_=archive();sha=hashlib.sha256(data).hexdigest()
        def fetch(url,limit,progress=None):
            if not url.startswith('https://mirror.example/'):raise OSError('origin blocked')
            if 'version.py' in url:return b"GAME_VERSION='0.1.0-alpha.6'\n"
            if 'SHA256SUMS' in url:return f'{sha}  SiliconImmortal-source.zip\n'.encode()
            if url.endswith('.zip'):return data
            raise OSError('unexpected request')
        r=check_updates('0.1.0-alpha.5',mirrors=['https://mirror.example/'],fetch=fetch)
        self.assertEqual(r['release']['source'],'proxy')
        with tempfile.TemporaryDirectory() as td:
            package=download_update(r['release'],Path(td),mirrors=['https://mirror.example/'],fetch=fetch)
            self.assertTrue((package['stage']/MANIFEST).is_file())

    def test_unpublished_proxy_main_is_not_reported_as_successfully_checked_release(self):
        def fetch(url,limit,progress=None):
            if url.startswith('https://mirror.example/') and 'version.py' in url:return b"GAME_VERSION='0.1.0-alpha.9'\n"
            raise OSError('no release assets or origin')
        with self.assertRaises(ValueError):check_updates('0.1.0-alpha.5',mirrors=['https://mirror.example/'],fetch=fetch)

    def test_zip_traversal_symlink_duplicates_and_checksum_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name in ('../escape','SiliconImmortal/../../escape','SiliconImmortal/.venv/x','SiliconImmortal/C:/x','SiliconImmortal/docs/WORKLOG.md',
                         'SiliconImmortal/docs/CON.txt','SiliconImmortal/tools/NUL.py','SiliconImmortal/assets/icon.png.','SiliconImmortal/assets/bad?.png'):
                data,_=archive({name:b'bad'})
                with self.subTest(name=name),self.assertRaises(ValueError):stage_archive(data,hashlib.sha256(data).hexdigest(),'0.1.0-alpha.6',root/name.replace('/','_').replace(':','_'))
            data,_=archive()
            with self.assertRaises(ValueError):stage_archive(data,'0'*64,'0.1.0-alpha.6',root/'badsha')
            buffer=io.BytesIO(data)
            with zipfile.ZipFile(buffer,'a') as z:
                item=zipfile.ZipInfo('SiliconImmortal/assets/link');item.external_attr=(0o120777<<16);z.writestr(item,b'/tmp')
            data=buffer.getvalue()
            with self.assertRaises(ValueError):stage_archive(data,hashlib.sha256(data).hexdigest(),'0.1.0-alpha.6',root/'link')

    def test_install_preserves_save_environment_user_files_and_backs_up_source(self):
        data,_=archive()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'app';root.mkdir();stage=Path(td)/'stage'
            (root/'silicon_professor').mkdir();(root/'silicon_professor/version.py').write_text('old')
            for rel in ('saves/save.json','.venv/keep','my-design.cor'):
                path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('preserve')
            stage_archive(data,hashlib.sha256(data).hexdigest(),'0.1.0-alpha.6',stage)
            result=apply_update(root,stage)
            self.assertIn('alpha.6',(root/'silicon_professor/version.py').read_text())
            for rel in ('saves/save.json','.venv/keep','my-design.cor'):self.assertEqual((root/rel).read_text(),'preserve')
            self.assertEqual((result['backup']/'silicon_professor/version.py').read_text(),'old')

    def test_git_checkout_symlink_parent_and_modified_manifest_are_not_overwritten(self):
        data,_=archive()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'app';root.mkdir();stage=Path(td)/'stage'
            stage_archive(data,hashlib.sha256(data).hexdigest(),'0.1.0-alpha.6',stage)
            (root/'.git').write_text('gitdir: elsewhere')
            with self.assertRaises(ValueError):apply_update(root,stage)
            (root/'.git').unlink();(root/'silicon_professor').symlink_to(Path(td)/'outside')
            with self.assertRaises(ValueError):apply_update(root,stage)
            (root/'silicon_professor').unlink();apply_update(root,stage)
            (root/'silicon_professor/version.py').write_text('my modified code')
            with self.assertRaises(ValueError):apply_update(root,stage)
            self.assertEqual((root/'silicon_professor/version.py').read_text(),'my modified code')

    def test_failed_transaction_rolls_back_before_restart(self):
        data,_=archive()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'app';root.mkdir();stage=Path(td)/'stage'
            (root/'silicon_professor').mkdir();(root/'silicon_professor/version.py').write_text('old')
            stage_archive(data,hashlib.sha256(data).hexdigest(),'0.1.0-alpha.6',stage)
            import os
            original=os.replace;failed=False
            def replace(src,dst):
                nonlocal failed
                if Path(dst)==root/'tools/bootstrap.py' and not failed:failed=True;raise OSError('injected disk error')
                return original(src,dst)
            with patch('silicon_professor.update_package.os.replace',side_effect=replace),self.assertRaises(OSError):apply_update(root,stage)
            self.assertEqual((root/'silicon_professor/version.py').read_text(),'old')
            self.assertFalse((root/MANIFEST).exists())
            self.assertFalse(recover_update(root))

    def test_failed_disk_flush_does_not_start_live_installation(self):
        data,_=archive()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'app';root.mkdir();stage=Path(td)/'stage'
            (root/'silicon_professor').mkdir();(root/'silicon_professor/version.py').write_text('old')
            stage_archive(data,hashlib.sha256(data).hexdigest(),'0.1.0-alpha.6',stage)
            with patch('silicon_professor.update_package.os.fsync',side_effect=OSError('flush failed')),self.assertRaises(OSError):
                apply_update(root,stage)
            self.assertEqual((root/'silicon_professor/version.py').read_text(),'old')
            self.assertFalse((root/MANIFEST).exists())

    def test_interrupted_journal_can_be_recovered_on_next_start(self):
        data,_=archive()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'app';root.mkdir();stage=Path(td)/'stage'
            (root/'silicon_professor').mkdir();(root/'silicon_professor/version.py').write_text('old')
            stage_archive(data,hashlib.sha256(data).hexdigest(),'0.1.0-alpha.6',stage)
            from silicon_professor import update_package
            original=update_package._atomic_copy
            def fail(source,target):
                if Path(target)==root/'tools/bootstrap.py':raise OSError('power interruption')
                return original(source,target)
            with patch.object(update_package,'_atomic_copy',side_effect=fail),patch.object(update_package,'recover_update',return_value=False),self.assertRaises(OSError):
                apply_update(root,stage)
            self.assertTrue((root/'.silicon-update-journal.json').exists())
            self.assertTrue(recover_update(root))
            self.assertEqual((root/'silicon_professor/version.py').read_text(),'old')
            self.assertFalse((root/MANIFEST).exists())

    def test_download_checksum_failure_falls_back_to_same_tag_proxy(self):
        data,_=archive();sha=hashlib.sha256(data).hexdigest()
        release=dict(source='forgejo',base='https://code.qiisme1021.space',version='0.1.0-alpha.6',tag='v0.1.0-alpha.6',
                     zip='https://code.qiisme1021.space/attachments/zip',checksum='https://code.qiisme1021.space/attachments/sha')
        def fetch(url,limit,progress=None):
            if 'code.qiisme' in url:return b'corrupt'
            if url.startswith('https://mirror.example/'):
                return data if url.endswith('.zip') else f'{sha}  SiliconImmortal-source.zip\n'.encode()
            raise OSError('GitHub blocked')
        with tempfile.TemporaryDirectory() as td:
            r=download_update(release,Path(td),mirrors=['https://mirror.example/'],fetch=fetch)
            self.assertEqual(r['source'],'https://mirror.example/')

    def test_source_archive_contains_manifest_but_excludes_internal_records(self):
        from tools import source_release
        data,_=archive({'SiliconImmortal/docs/WORKLOG.md':b'internal'})
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'docs/player-guide').mkdir(parents=True);(root/'docs/player-guide/index.html').write_text('manual')
            with patch.object(source_release,'ROOT',root),patch.object(source_release.subprocess,'check_output',return_value=data):source_release.main()
            archive_data=(root/'release-assets/SiliconImmortal-source.zip').read_bytes()
            with zipfile.ZipFile(io.BytesIO(archive_data)) as z:
                self.assertIn('SiliconImmortal/'+MANIFEST,z.namelist())
                self.assertNotIn('SiliconImmortal/docs/WORKLOG.md',z.namelist())
            stage_archive(archive_data,hashlib.sha256(archive_data).hexdigest(),'0.1.0-alpha.6',root/'staged')
