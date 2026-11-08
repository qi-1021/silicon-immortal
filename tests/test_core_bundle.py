import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from silicon_professor import export
from silicon_professor.data.blocks import GPUS, NPUS, FIXED_BLOCKS, get_gpu, get_npu, get_isp
from silicon_professor.data.cores import CORES, get_ip
from silicon_professor.data.nodes import NODES
from silicon_professor.data.core_designs import default_hardware
from silicon_professor.engine.ip_library import make_design_asset, attach_asset
from silicon_professor.engine.simulate import simulate
from silicon_professor.engine.types import empty_design


class TestCoreBundle(unittest.TestCase):
    def read(self, record):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'portable.sil'
            path.write_text(json.dumps(record), encoding='utf-8')
            return export.read_design(path)

    def test_export_contains_complete_template_names_and_models_without_mutation(self):
        design = empty_design('sandbox')
        before = copy.deepcopy(design.to_dict())
        record = export.payload(design, None)
        templates = record['design']['core_templates']
        for kind, ident, model in [('cpu', 'x925', CORES['x925']),
                                   ('gpu', 'g925', GPUS['g925']),
                                   ('npu', 'npu30', NPUS['npu30']),
                                   ('isp', 'isp', FIXED_BLOCKS['isp'])]:
            snap = templates[kind+':'+ident]
            self.assertEqual(snap['name'], model['name'])
            self.assertEqual(snap['model'], model)
        self.assertEqual(design.to_dict(), before)
        self.assertEqual(record['core_bundle']['schema'], 'embedded-cores-v1')

    def test_template_catalog_removal_does_not_change_import_or_reexport(self):
        design = empty_design('sandbox'); result = simulate(design)
        record = export.payload(design, result)
        with patch.dict(CORES, {}, clear=True), patch.dict(GPUS, {}, clear=True), \
                patch.dict(NPUS, {}, clear=True), patch.dict(FIXED_BLOCKS, {'isp': {'name': 'changed'}}):
            imported, _ = self.read(record)
            replay = simulate(imported)
            self.assertEqual(get_ip(imported, 'x925')['name'], CORES.get('x925', {}).get('name', 'Cortex-X925'))
            self.assertEqual(replay['die_area'], result['die_area'])
            self.assertEqual(replay['perf'], result['perf'])
            self.assertEqual(export.payload(imported, replay)['design']['core_templates'], record['design']['core_templates'])

    def test_mixed_template_and_cor_definitions_travel_in_one_file(self):
        design = empty_design('sandbox')
        h = default_hardware('cpu'); h['architecture'] = 'aarch64'
        cpu = make_design_asset('cpu', '我的应用核', h)
        attach_asset(design, cpu)
        npu = make_design_asset('npu', '我的阵列', default_hardware('npu'))
        attach_asset(design, npu)
        imported, _ = self.read(export.payload(design, None))
        self.assertEqual(imported.embedded_ips[cpu['id']]['design'], cpu['design'])
        self.assertEqual(get_ip(imported, 'ip:'+cpu['id'])['name'], cpu['name'])
        self.assertEqual(get_npu(imported)['name'], npu['name'])
        self.assertEqual(get_gpu(imported)['name'], GPUS['g925']['name'])
        self.assertEqual(get_isp(imported)['name'], FIXED_BLOCKS['isp']['name'])

    def test_saved_reference_process_parameters_survive_catalog_changes(self):
        design = empty_design('sandbox')
        design.cores[0].core_id = 'a76'; design.gpu_id = 'g715'
        result = simulate(design); record = export.payload(design, result)
        with patch.dict(NODES, {'n7': dict(NODES['n7'], area_scale=999, freq_scale=999),
                                'n4p': dict(NODES['n4p'], area_scale=999, freq_scale=999)}):
            imported, _ = self.read(record)
            self.assertEqual(simulate(imported)['die_area'], result['die_area'])

    def test_sil_keeps_bound_custom_accelerators_when_local_templates_removed(self):
        design = empty_design('sandbox')
        for kind in ('gpu', 'npu', 'isp'):
            attach_asset(design, make_design_asset(kind, '我的'+kind, default_hardware(kind)))
        record = export.payload(design, None)
        with patch.dict(GPUS, {}, clear=True), patch.dict(NPUS, {}, clear=True):
            imported, _ = self.read(record)
            self.assertEqual(imported.ip_blocks, design.ip_blocks)

    def test_missing_or_corrupt_snapshot_reports_dependency_instead_of_fallback(self):
        record = export.payload(empty_design('sandbox'), None)
        for mutate in ('missing', 'digest', 'kind', 'zero'):
            bad = copy.deepcopy(record)
            snap = bad['design']['core_templates']['cpu:x925']
            if mutate == 'missing': del bad['design']['core_templates']['cpu:x925']
            if mutate == 'digest': snap['name'] = 'corrupted'
            if mutate == 'kind': snap['kind'] = 'gpu'
            if mutate == 'zero': snap['model']['fmax_ref'] = 0
            with self.subTest(mutate=mutate), self.assertRaisesRegex(ValueError, 'cpu:x925'):
                self.read(bad)

    def test_legacy_sil_without_bundle_reads_with_catalog_notice(self):
        record = export.payload(empty_design('sandbox'), None)
        record.pop('core_bundle', None); record['design'].pop('core_templates', None)
        design, notes = self.read(record)
        self.assertEqual(get_ip(design, 'x925')['name'], CORES['x925']['name'])
        self.assertTrue(any('模板' in note for note in notes))

    def test_complete_bundle_cannot_replace_missing_legacy_custom_core_with_defaults(self):
        design=empty_design('sandbox');design.cores[0].core_id='custom';design.custom.name='旧自研核心'
        record=export.payload(design,None)
        record['design'].pop('custom')
        with self.assertRaisesRegex(ValueError,'custom'):self.read(record)
