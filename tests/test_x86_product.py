import unittest
from silicon_professor.engine.types import empty_design
from silicon_professor.engine.simulate import simulate
from silicon_professor.data.cores import get_ip
from silicon_professor.data.core_designs import FIELDS
from silicon_professor.engine.core_studio import run_design,hardware_from_template


class TestX86Product(unittest.TestCase):
    def test_x86_project_has_reusable_template_hardware_and_valid_soc(self):
        d=empty_design('x86_workstation');r=simulate(d)
        self.assertTrue(r['signoff']['ready'],r['errors'])
        self.assertTrue(all(get_ip(d,g.core_id)['isa']=='x86_64' for g in d.cores))
        for g in d.cores:
            h=hardware_from_template(get_ip(d,g.core_id))
            result=run_design('cpu',h,{'source':'MOV EAX,6\nMOV EBX,7\nIMUL EAX,EBX\nMOV [0],EAX\nMOV ECX,[0]\nHALT'})
            self.assertEqual(dict(zip(result['register_names'],result['registers']))['ECX'],42)

    def test_isa_picker_leads_with_familiar_name_and_explains_width(self):
        field=next(f for f in FIELDS['cpu'] if f['key']=='architecture')
        labels=dict(field['options'])
        self.assertIn('32',labels['x86_32']);self.assertIn('Intel',labels['x86_32'])
        self.assertIn('RISC-V',labels['riscv32']);self.assertIn('64',labels['aarch64'])
        self.assertIn('64',labels['x86_64'])
