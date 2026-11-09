import unittest
from silicon_professor.data.core_experiments import EXPERIMENTS,experiment_preset
from silicon_professor.engine.core_studio import run_design


class TestCoreExperiments(unittest.TestCase):
    def test_presets_are_runnable_and_stay_independent(self):
        for key in EXPERIMENTS:
            p=experiment_preset(key);r=run_design(p['kind'],p['hardware'],p['bench'])
            self.assertTrue(r['functional_check'],key)
            self.assertGreater(r['cycles'],0)
            p['name']='changed'
            self.assertNotEqual(experiment_preset(key)['name'],'changed')

    def test_smt_and_miss_slots_are_actual_shared_resource_comparisons(self):
        p=experiment_preset('smt');r=run_design(p['kind'],p['hardware'],p['bench'])
        self.assertGreater(r['speedup'],1)
        p=experiment_preset('mshr');many=run_design(p['kind'],p['hardware'],p['bench'])
        p['hardware']['mshrs']=1;one=run_design(p['kind'],p['hardware'],p['bench'])
        self.assertLess(many['cycles'],one['cycles'])
