import unittest
from silicon_professor.engine.rescue_performance import performance_contract,evaluate_performance


class TestRescuePerformance(unittest.TestCase):
    def test_seventy_percent_loss_fails_even_when_stability_looks_perfect(self):
        contract=performance_contract('rescue_tensor_g6')
        candidate={key:rule['baseline']*.3 for key,rule in contract.items() if rule['kind']=='throughput'}
        candidate['gpu_stability']=1.0
        result=evaluate_performance(contract,candidate)
        self.assertFalse(result['ready'])
        self.assertFalse(next(c['ok'] for c in result['checks'] if c['id']=='single'))
        self.assertFalse(next(c['ok'] for c in result['checks'] if c['id']=='gpu_peak'))

    def test_810_absolute_fps_floor_rejects_low_peak_high_ratio(self):
        c=performance_contract('rescue_810')
        self.assertEqual(c['gpu_peak']['baseline'],50)
        self.assertAlmostEqual(c['gpu_peak']['minimum'],42.5)
        self.assertFalse(evaluate_performance(c,dict(gpu_peak=15,gpu_sustain=15))['ready'])
        r=evaluate_performance(c,dict(gpu_peak=48,gpu_sustain=35))
        self.assertTrue(next(c['ok'] for c in r['checks'] if c['id']=='gpu_peak'))
        self.assertFalse(r['ready']) # CPU measurements still missing: no whole-chip certification.

    def test_gb6_uses_specific_major_minor_record_and_never_cross_version(self):
        c=performance_contract('rescue_tensor_g2')
        self.assertEqual(c['single']['baseline'],1465)
        self.assertEqual(c['multi']['baseline'],3967)
        self.assertEqual(c['single']['version'],'6.7')
        self.assertFalse(evaluate_performance(c,dict(single=3000,multi=9000,gpu_stability=.8),benchmark_version='5.5')['ready'])

    def test_missing_benchmarks_do_not_receive_a_default_score(self):
        c=performance_contract('rescue_8ee6');self.assertEqual(c,{})
        self.assertFalse(evaluate_performance(c,{})['ready'])
        c=performance_contract('rescue_tensor_g6')
        self.assertFalse(evaluate_performance(c,dict(single=4000,multi=9000))['ready'])

    def test_sata_four_devices_with_slow_bridge_do_not_pass_performance(self):
        from silicon_professor.engine.rescue import run_rescue
        r=run_rescue('rescue_cougar',dict(ports='disable_3g',external=True,external_bandwidth_gbps=1.0))
        self.assertEqual(r['metrics']['usable_devices'],4)
        self.assertFalse(r['ready'])
        self.assertFalse(next(c['ok'] for c in r['checks'] if c['id']=='performance_retention'))
        r=run_rescue('rescue_cougar',dict(ports='disable_3g',external=True,external_bandwidth_gbps=6.0))
        self.assertTrue(r['ready'])
