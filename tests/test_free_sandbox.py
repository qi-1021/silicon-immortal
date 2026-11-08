import unittest
from silicon_professor.engine.types import empty_design,CoreGroup
from silicon_professor.engine.simulate import simulate


class TestFreeSandbox(unittest.TestCase):
    def test_free_mode_reports_problems_without_product_tapeout_gate(self):
        d=empty_design('sandbox');d.cores=[CoreGroup('x64_wide',2,1.,False,5.)]
        d.pdn_resistance_mohm=100;d.verification_effort=0
        r=simulate(d)
        self.assertTrue(r['signoff']['ready'])
        self.assertTrue(r['signoff']['diagnostics'])
        self.assertEqual(r['signoff']['blockers'],[])
        self.assertTrue(all(c['explanation'] and c['remedy'] for c in r['signoff']['diagnostics']))
        self.assertAlmostEqual(r['engineering']['pdn_resistance_ohm'],.1)

    def test_regular_project_still_uses_required_signoff(self):
        d=empty_design('x86_workstation');d.pdn_resistance_mohm=100
        r=simulate(d)
        self.assertFalse(r['signoff']['ready'])
        self.assertTrue(any(c['id']=='pdn' for c in r['signoff']['blockers']))

    def test_x64_core_and_pdn_definition_survive_soc_file(self):
        import tempfile
        from pathlib import Path
        from silicon_professor.export import export_to,read_design
        from silicon_professor.data.core_designs import default_hardware
        from silicon_professor.engine.ip_library import make_design_asset,attach_asset
        d=empty_design('sandbox');d.cores=[];d.pdn_resistance_mohm=3.5
        asset=make_design_asset('cpu','64位应用核',default_hardware('cpu')|dict(architecture='x86_64'))
        attach_asset(d,asset)
        with tempfile.TemporaryDirectory() as td:
            p=export_to(Path(td)/'x64.sil',d,simulate(d));loaded,_=read_design(p)
            self.assertEqual(loaded.pdn_resistance_mohm,3.5)
            self.assertEqual(loaded.embedded_ips[asset['id']]['design'],asset['design'])
