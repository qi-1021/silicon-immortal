import unittest
from silicon_professor.data.blueprints import BLUEPRINT_BY_ID,BLUEPRINTS
from silicon_professor.data.cores import CORES
from silicon_professor.data.blocks import GPUS
from silicon_professor.data.sources import SOURCES


class TestCatalogAccuracy(unittest.TestCase):
    def test_a20_does_not_relabel_a19_and_has_separate_neural_architecture(self):
        a19=BLUEPRINT_BY_ID['a19pro'];a20=BLUEPRINT_BY_ID['a20pro']
        ids19={g[0] for g in a19['build']['cores']};ids20={g[0] for g in a20['build']['cores']}
        self.assertFalse(ids19&ids20)
        self.assertNotIn('Sawtooth',a20['cpu']);self.assertNotIn('A19',a20['cpu'])
        self.assertEqual(a20['build']['gpu'][1],7)
        self.assertEqual(a20['hardware_facts']['cpu_neural_accelerators'],True)
        self.assertEqual(a20['hardware_facts']['neural_engine_cores'],32)
        self.assertNotEqual(a19['hardware_facts']['cpu_neural_accelerators'],a20['hardware_facts']['cpu_neural_accelerators'])

    def test_qualcomm_blueprints_never_silently_instantiate_mali(self):
        for cid in ('sd855','sd888','sd8g2','sd8g3','sd8elite5','sd8elite6'):
            bp=BLUEPRINT_BY_ID[cid];gpu=GPUS[bp['build']['gpu'][0]]
            self.assertEqual(gpu['vendor'],'Qualcomm',cid)
        bp=BLUEPRINT_BY_ID['sd8elite6']
        self.assertNotIn('Oryon 3',bp['cpu'])
        self.assertEqual([g[3] for g in bp['build']['cores']],[5.0,4.0])
        self.assertIn('Flex',bp['cache'])

    def test_tensor_g4_gpu_matches_seven_core_spec_and_g6_layout_matches_seven_cpus(self):
        g4=BLUEPRINT_BY_ID['tensorG4'];self.assertIn('MP7',g4['gpu'])
        self.assertEqual(g4['build']['gpu'][1],7)
        g6=BLUEPRINT_BY_ID['tensorG6'];self.assertEqual(sum(g[1] for g in g6['build']['cores']),7)
        self.assertFalse(any('Nano' in block['label'] or 'G1 Ultra' in block['label'] for block in g6['layout']))

    def test_all_catalog_entries_separate_asserted_facts_from_game_values(self):
        for bp in BLUEPRINTS:
            self.assertIn('hardware_facts',bp,bp['id'])
            self.assertIn('assumption_fields',bp)
            for sid in bp['hardware_facts'].get('sources',[]):self.assertIn(sid,SOURCES)
        for key in ('a17p','a17e','a19e','a20p','a20e','m4e','m5e','oryon6_prime','oryon6_performance'):
            self.assertIn(key,CORES)
            self.assertEqual(CORES[key]['parameter_basis'],'game_assumption')

    def test_existing_public_core_exports_include_all_new_records(self):
        from silicon_professor.data.cores import CORE_LIST,CORE_BY_ID,LICENSABLE,RESEARCH
        self.assertEqual(set(CORE_BY_ID),set(CORES))
        self.assertEqual(LICENSABLE,{c['id'] for c in CORE_LIST})
        self.assertTrue(any(c['id']=='a20p' for c in RESEARCH))

    def test_apple_application_processor_layouts_never_contain_cellular_modem(self):
        for cid in ('a17pro','a19pro','a20pro','m1','m4','m5'):
            with self.subTest(chip=cid):
                bp=BLUEPRINT_BY_ID[cid]
                self.assertFalse(any(block['k']=='modem' for block in bp['layout']))
                self.assertFalse(bp['hardware_facts']['integrated_cellular_modem'])
                self.assertEqual(bp['build']['modem'],'modem_ext' if cid.startswith('a') else 'modem_none')
