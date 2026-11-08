import json
import unittest
from pathlib import Path
from unittest.mock import patch
from silicon_professor.engine.rtl import test_picorv32,rtl_info,BUNDLE


class TestRealRTL(unittest.TestCase):
    def test_missing_runtime_does_not_claim_passed(self):
        with patch('silicon_professor.engine.rtl.shutil.which',return_value=None):
            self.assertEqual(test_picorv32()['status'],'unavailable')

    def test_upstream_hash_and_license_are_retained(self):
        import hashlib
        info=rtl_info()
        self.assertEqual(info['license'],'ISC')
        for name,sha in info['sha256'].items():
            self.assertEqual(hashlib.sha256((BUNDLE/name).read_bytes()).hexdigest(),sha)
        self.assertIn('Permission to use, copy, modify',(BUNDLE/'COPYING').read_text(encoding="utf-8"))


if __name__=='__main__':unittest.main()
