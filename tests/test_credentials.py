"""Exercise only local assertion tasks; never connect to inventory hosts."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('vmware_snapshot', {}, False),
    ('vmware_snapshot', {'esxi_password': 'fixture-only-long-password'}, True),
    ('vmware_snapshot', {'esxi_password': 'your_esxi_password_here'}, False),
    ('vmware_snapshot', {'esxi_password': 'fixture-only-long-password', 'esxi_validate_certs': False}, False),
]
GROUPS = {'vmware_snapshot': 'all'}

class CredentialPreflightTests(unittest.TestCase):
    def test_credentials_fail_closed_before_deployment(self):
        for role, values, accepted in CASES:
            with self.subTest(role=role, accepted=accepted), tempfile.TemporaryDirectory() as folder:
                play = Path(folder) / 'preflight.yml'
                group = 'group_vars/' + GROUPS[role] + '.yml'
                play.write_text(json.dumps([{
                    'hosts': 'localhost', 'gather_facts': False, 'become': False,
                    'vars_files': [str(ROOT / 'roles' / role / 'defaults/main.yml'), str(ROOT / group)],
                    'tasks': [{'ansible.builtin.import_tasks': str(ROOT / 'roles' / role / 'tasks/validate.yml')}],
                }]))
                env = dict(os.environ, ANSIBLE_STDOUT_CALLBACK='default', ANSIBLE_LOCAL_TEMP=folder)
                result = subprocess.run([
                    'ansible-playbook', '-i', 'localhost,', '-c', 'local', str(play),
                    '--extra-vars', json.dumps(values),
                ], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
                if result.returncode not in (0, 2):
                    self.fail('Ansible validation could not run: ' + result.stderr)
                self.assertEqual(result.returncode == 0, accepted, result.stdout)

if __name__ == '__main__':
    unittest.main()
