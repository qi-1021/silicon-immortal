import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from silicon_professor import __version__,export
from silicon_professor.engine.ip_library import make_asset,read_asset,write_asset
from silicon_professor.engine.labs import DEFAULTS
from silicon_professor.engine.types import empty_design
from silicon_professor.version import MODEL_VERSION


class TestFileCompatibility(unittest.TestCase):
    def test_export_model_identifiers_agree(self):
        record=export.payload(empty_design('sandbox'),None)
        self.assertEqual(record['engine']['model'],MODEL_VERSION)
        self.assertEqual(record['producer']['model'],MODEL_VERSION)

    def _read_record(self, record):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'test.sil'
            path.write_text(json.dumps(record),encoding='utf-8')
            return export.read_design(path)

    def test_soc_invalid_numbers_report_field_and_source_version(self):
        for field,value in [('ambient_c',float('nan')),('l3_mb',-1),
                            ('memory_channels',-1),('gpu_units',1.5),
                            ('workload_parallel',1.1),('pdn_quality',float('inf'))]:
            with self.subTest(field=field):
                record=export.payload(empty_design('sandbox'),None)
                record['producer']['version']='future-test'
                record['design'][field]=value
                with self.assertRaisesRegex(ValueError,field) as caught:self._read_record(record)
                self.assertIn('future-test',str(caught.exception))

    def test_soc_rejects_malformed_nested_data_and_unknown_ids(self):
        for field,value in [('cores',[None]),('placements',[]),('custom',[]),
                            ('gpu_id','unknown-gpu'),('node_id','unknown-node'),
                            ('isp','false')]:
            with self.subTest(field=field):
                record=export.payload(empty_design('sandbox'),None)
                record['design'][field]=value
                with self.assertRaisesRegex(ValueError,field):self._read_record(record)

    def test_soc_bounds_core_count_before_simulation(self):
        record=export.payload(empty_design('sandbox'),None)
        record['design']['cores'][0]['count']=1000000000
        with patch('silicon_professor.engine.simulate.simulate',side_effect=AssertionError('must validate before simulation')):
            with self.assertRaisesRegex(ValueError,'cores\\[0\\].count'):self._read_record(record)

    def test_soc_reports_bad_placement_and_missing_cpu_asset(self):
        record=export.payload(empty_design('sandbox'),None)
        record['design']['placements']={'core:0:0':{'x':float('inf'),'y':0}}
        with self.assertRaisesRegex(ValueError,'placements.*x'):self._read_record(record)
        record['design']['placements']={}
        record['design']['cores'][0]['core_id']='ip:missing'
        with self.assertRaisesRegex(ValueError,'cores.*core_id'):self._read_record(record)

    def test_soc_unknown_fields_and_unfinished_design_remain_editable(self):
        record=export.payload(empty_design('sandbox'),None)
        record['design']['future_config']={'hint':'not simulated'}
        record['design']['cores']=[]
        design,notes=self._read_record(record)
        self.assertEqual(design.cores,[])
        self.assertTrue(any('future_config' in note for note in notes))

    def test_sil_has_alpha_producer_and_imports_newer_version(self):
        d=empty_design('sandbox');d.name='我的SoC'
        with tempfile.TemporaryDirectory() as td:
            path=export.export_to(Path(td)/'chip',d,None)
            self.assertEqual(path.suffix,'.sil')
            record=json.loads(path.read_text())
            self.assertIn('alpha',record['producer']['version'])
            self.assertEqual(record['producer']['version'],__version__)
            record['producer']['version']='9.0.0';record['version']=99;record['future_note']='anything'
            path.write_text(json.dumps(record))
            imported,notices=export.read_design(path)
            self.assertEqual(imported.name,d.name)
            self.assertTrue(notices)

    def test_cor_keeps_versions_diagnostic_and_validates_contents(self):
        a=make_asset('cpu','core',DEFAULTS['cpu'])
        with tempfile.TemporaryDirectory() as td:
            p=write_asset(Path(td)/'core',a)
            self.assertEqual(p.suffix,'.cor')
            record=json.loads(p.read_text());self.assertEqual(record['producer']['version'],__version__)
            record['version']=99;record['producer']['version']='9.0.0';record['optional_description']='future'
            p.write_text(json.dumps(record))
            r=read_asset(p);self.assertEqual(r['name'],'core');self.assertIn('optional_description',r)
            self.assertTrue(r['compatibility_notes'])
            record['config']['width']=999999999;p.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,'9.0.0'):read_asset(p)

    def test_old_design_and_cor_are_readable(self):
        d=empty_design('sandbox');record=export.payload(d,None);record.pop('producer',None)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'old.spchip.json';p.write_text(json.dumps(record));restored,notes=export.read_design(p)
            self.assertEqual(restored.node_id,d.node_id)
            a=make_asset('cpu','old',DEFAULTS['cpu']);a.pop('producer',None)
            p=Path(td)/'old.spip.json';p.write_text(json.dumps(a));self.assertEqual(read_asset(p)['name'],'old')

    def test_unknown_optional_config_preserved_and_legacy_defaults(self):
        import hashlib
        from silicon_professor.engine.ip_library import canonical,asset_model
        a=make_asset('cpu','future',DEFAULTS['cpu']);a['config']['future_annotation']='info'
        digest=hashlib.sha256(canonical(dict(kind=a['kind'],name=a['name'],config=a['config'])).encode()).hexdigest()
        a.update(digest=digest,id=digest[:32],version=2)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'future.cor';p.write_text(json.dumps(a));loaded=read_asset(p)
            self.assertEqual(loaded['config']['future_annotation'],'info')
            self.assertGreater(asset_model(loaded)['fmax_ref'],0)
            a['config'].pop('architecture');a['config'].pop('future_annotation')
            digest=hashlib.sha256(canonical(dict(kind=a['kind'],name=a['name'],config=a['config'])).encode()).hexdigest();a.update(digest=digest,id=digest[:32])
            p.write_text(json.dumps(a));self.assertEqual(read_asset(p)['name'],'future')


if __name__=='__main__':unittest.main()
