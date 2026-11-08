import copy
import json
import tempfile
import unittest
from pathlib import Path
from silicon_professor.engine.ip_library import make_asset,read_asset,write_asset,attach_asset,asset_model
from silicon_professor.engine.labs import DEFAULTS
from silicon_professor.engine.types import Design,empty_design
from silicon_professor.engine.simulate import simulate


class TestIPLibrary(unittest.TestCase):
    def test_ia32_asset_does_not_claim_64bit_execution(self):
        config=dict(DEFAULTS['cpu'],architecture='x86_32',extensions=[],source='MOV EAX,42\nHALT')
        asset=make_asset('cpu','IA-32',config)
        self.assertEqual(asset_model(asset)['isa'],'x86_32')
        design=empty_design('sandbox');design.cores=[]
        attach_asset(design,asset);attach_asset(design,asset)
        self.assertTrue(simulate(design)['valid'])
        design.cores.append(empty_design('sandbox').cores[0])
        self.assertTrue(any('x86' in message for message in simulate(design)['errors']))

    def test_named_cpu_roundtrip_embedded_soc_and_multiple_instances(self):
        a=make_asset('cpu','我的实验核',DEFAULTS['cpu'])
        d=empty_design('sandbox');d.cores=[];attach_asset(d,a);attach_asset(d,a)
        self.assertEqual(d.cores[0].core_id,d.cores[1].core_id)
        r=simulate(d);self.assertTrue(r['valid'],r['errors']);self.assertEqual(r['groups'][0]['ip']['name'],'我的实验核')
        restored=Design.from_dict(d.to_dict());self.assertEqual(simulate(restored)['groups'][0]['ip']['name'],'我的实验核')
        with tempfile.TemporaryDirectory() as td:
            p=write_asset(Path(td)/'core.spip.json',a);loaded=read_asset(p)
            self.assertEqual(loaded['id'],a['id']);self.assertEqual(loaded['verification']['passed'],True)

    def test_import_tampering_and_unimplemented_extensions_rejected(self):
        a=make_asset('cpu','core',DEFAULTS['cpu']);bad=copy.deepcopy(a);bad['config']['extensions']=['AVX']
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.json';p.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):read_asset(p)

    def test_gpu_npu_isp_are_used_in_plan(self):
        for kind in ('gpu','npu','isp'):
            a=make_asset(kind,'my '+kind,DEFAULTS[kind]);d=empty_design('sandbox');attach_asset(d,a);r=simulate(d)
            self.assertTrue(r['valid'],r['errors'])
            self.assertTrue(any(a['name'] in b.label for b in r['plan'].blocks),kind)

    def test_core_library_does_not_modify_other_designs(self):
        a=make_asset('cpu','private',DEFAULTS['cpu']);first=empty_design('sandbox');second=empty_design('sandbox')
        first.cores=[]
        attach_asset(first,a);self.assertFalse(second.embedded_ips)

    def test_overflowing_or_oversized_npu_cannot_be_saved_as_verified(self):
        p=dict(DEFAULTS['npu'],m=32,n=32,k=64,rows=32,cols=32,scratchpad_kb=1)
        with self.assertRaises(ValueError):make_asset('npu','bad',p)


if __name__=='__main__':unittest.main()
