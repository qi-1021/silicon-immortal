import json
import tempfile
import unittest
from pathlib import Path

from silicon_professor.data.rescue import RESCUE_CASES, reference_controls
from silicon_professor.data.sources import SOURCES
from silicon_professor.engine.rescue import run_rescue, export_rescue, read_rescue


class TestRescue(unittest.TestCase):
    def test_each_case_has_scope_conditions_and_failing_start_passing_reference(self):
        self.assertGreaterEqual(len(RESCUE_CASES),10)
        for cid,case in RESCUE_CASES.items():
            with self.subTest(case=cid):
                self.assertTrue(case['history']);self.assertTrue(case['conditions']);self.assertTrue(case['scope'])
                self.assertTrue(all(s in SOURCES for s in case['sources']))
                self.assertFalse(run_rescue(cid)['ready'])
                r=run_rescue(cid,reference_controls(cid))
                if case.get('experiment_status')=='model_pending':
                    self.assertFalse(r['ready']);self.assertIn('chip',r);continue
                self.assertTrue(r['ready'],r['checks'])
                self.assertEqual(r['parameter_basis'],'game_assumption')
                self.assertFalse(r['calibrated'])

    def test_divider_missed_coverage_is_not_a_fix(self):
        r=run_rescue('rescue_fdiv',dict(coverage='basic',divider='missing_entry'))
        self.assertTrue(all(row[-1] for row in r['rows']))
        self.assertFalse(r['ready'])
        r=run_rescue('rescue_fdiv',dict(coverage='boundary',divider='missing_entry'))
        self.assertTrue(any(not row[-1] for row in r['rows']))

    def test_tlb_workaround_has_cost_and_hardware_revision_restores_overlap(self):
        safe=run_rescue('rescue_barcelona',dict(policy='serialize',stress=True))
        revised=run_rescue('rescue_barcelona',dict(policy='revised',stress=True))
        self.assertFalse(safe['ready']);self.assertTrue(revised['ready'])
        self.assertGreater(safe['metrics']['cycles'],revised['metrics']['cycles'])
        self.assertFalse(next(c['ok'] for c in safe['checks'] if c['id']=='performance_retention'))
        self.assertFalse(run_rescue('rescue_barcelona',dict(policy='unchecked',stress=True))['ready'])

    def test_sata_isolation_requires_enough_usable_devices(self):
        r=run_rescue('rescue_cougar',dict(ports='disable_3g',external=False))
        self.assertFalse(r['ready'])
        r=run_rescue('rescue_cougar',dict(ports='disable_3g',external=True))
        self.assertTrue(r['ready']);self.assertEqual(r['metrics']['external_devices'],2)

    def test_mobile_cooling_change_is_device_experiment_not_chip_fix(self):
        chip=run_rescue('rescue_888',reference_controls('rescue_888'))
        self.assertFalse(chip['ready'])
        cooling=run_rescue('rescue_888',dict(thermal_r=2.0))
        self.assertFalse(cooling['ready'])
        self.assertNotIn('steady_c',cooling['metrics'])
        self.assertIn('原始测量',cooling['consequence'])
        self.assertFalse(run_rescue('rescue_888',dict(frequency_ghz=3.5,voltage=.7))['ready'])

    def test_parameters_are_strict_and_portable_results_are_recomputed(self):
        for bad in ({'magic':1},{'frequency_ghz':float('nan')},{'frequency_ghz':True},{'thermal_r':-1}):
            with self.assertRaises(ValueError):run_rescue('rescue_888',bad)
        with tempfile.TemporaryDirectory() as td:
            path=export_rescue(Path(td)/'rescue.json','rescue_fdiv',reference_controls('rescue_fdiv'))
            self.assertTrue(read_rescue(path)['ready'])
            record=json.loads(path.read_text());record['result']['ready']=True
            record['parameters']={'coverage':'boundary','divider':'missing_entry'}
            path.write_text(json.dumps(record))
            self.assertFalse(read_rescue(path)['ready'])

    def test_pentium_uses_documented_divisor_columns_and_srt_bound(self):
        r=run_rescue('rescue_fdiv',dict(coverage='boundary',divider='missing_entry'))
        rows=r['rows'][2:]
        self.assertEqual([row[0] for row in rows],['17/16','5/4','23/16','13/8','29/16'])
        self.assertTrue(all(row[2]==2 and row[3]==0 and not row[-1] for row in rows))
        software=run_rescue('rescue_fdiv',dict(coverage='boundary',divider='software'))
        self.assertFalse(software['ready'])
        self.assertLess(software['metrics']['performance_retention'],.85)

    def test_pending_mobile_dossiers_are_not_identical_or_fake_successes(self):
        from silicon_professor.data.rescue_measurements import MOBILE_CHIPS
        self.assertEqual(MOBILE_CHIPS['rescue_tensor_g2']['gpu'],'Mali-G710 MP7')
        self.assertEqual(MOBILE_CHIPS['rescue_tensor_g5']['gpu'],'PowerVR DXT-48-1536')
        self.assertNotEqual(MOBILE_CHIPS['rescue_tensor_g2']['cpu'],MOBILE_CHIPS['rescue_tensor_g3']['cpu'])
        for cid in MOBILE_CHIPS:
            r=run_rescue(cid);self.assertFalse(r['ready']);self.assertEqual(r['parameter_basis'],'source_record')
