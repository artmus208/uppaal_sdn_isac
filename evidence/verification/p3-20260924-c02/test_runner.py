"""Regression checks for the C02 timeout and executable handoff; no model checking."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import yaml

RUNNER = Path(__file__).resolve().parents[1] / 'p3-20260923' / 'run.py'
spec = importlib.util.spec_from_file_location('p3_runner', RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RunnerTimeoutTests(unittest.TestCase):
    def test_positive_timeout_required(self):
        for value in ['0', '-1', 'nan', '1.5']:
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    runner.parse_args(['--run-id', 'test', '--timeout-seconds', value])

    def test_timeout_and_executable_reach_native_config_and_wrapper(self):
        for seconds in [60, 600]:
            with self.subTest(seconds=seconds), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / 'manifests/baselines').mkdir(parents=True)
                (root / 'model.xml').write_text('<nta/>')
                query = 'A[] (!mac_obs_ack_late && (mac_obs_ack_active imply mac_c_obs_ack <= mac_D_phy_ack))'
                (root / 'selected-queries.q').write_text(query + '\n')
                (root / 'selected-queries.json').write_text(json.dumps([
                    {'id': 'C02-ack-elapsed', 'query': query, 'role': 'bounded-response-safety'},
                ]))
                for filename in ['parameters.json', 'instance-vector.json']:
                    (root / filename).write_text('{}')
                executable = root / 'Program Files' / 'verifyta.exe'
                executable.parent.mkdir()
                executable.touch()
                manifest = {
                    'metadata': {'frozen': True, 'id': 'test-only'},
                    'gate_1': {'passed': True},
                    'hashing': {'common_hashes': {k: {'value': 'test'} for k in ['source_hash', 'generator_hash']}},
                    'model_topology': {'integrated_model': {'path': 'model.xml', 'sha256': runner.sha((root/'model.xml').read_bytes())}},
                    'verification_configuration': {
                        'canonical_query_set': {'path': 'selected-queries.q', 'sha256': runner.sha((root/'selected-queries.q').read_bytes())},
                        'canonical_parameter_set': {'path': 'parameters.json'},
                        'canonical_instance_vector': {'path': 'instance-vector.json'},
                        'uppaal': {'version': 'test-version'},
                    },
                }
                (root/'manifests/baselines/reviewer-r1.yaml').write_text(yaml.safe_dump(manifest))
                argv = ['--run-id', 'test-only', '--ids', 'C02-ack-elapsed', '--verifyta', str(executable)]
                if seconds != 60:
                    argv += ['--timeout-seconds', str(seconds)]
                args = runner.parse_args(argv)
                calls = []

                def fake_run(command, **kwargs):
                    calls.append((command, kwargs))
                    if command[-1] == '--version':
                        self.assertEqual(command[0], str(executable))
                        self.assertEqual(kwargs['cwd'], executable.parent)
                        return subprocess.CompletedProcess(command, 0, b'test-version\n', b'')
                    if '-Command' in command:
                        return subprocess.CompletedProcess(command, 0, b'{}', b'')
                    if '-Config' in command:
                        config = json.loads(Path(command[-1]).read_text())
                        self.assertEqual(config['timeout_seconds'], seconds)
                        self.assertEqual(kwargs['timeout'], seconds + 30)
                        self.assertEqual(config['executable'], str(executable))
                        self.assertEqual(config['arguments'][:4], ['-o', '0', '-t', '1'])
                        self.assertEqual(Path(config['arguments'][-1]).read_text(), query+'\n')
                        Path(config['stdout']).write_text('')
                        Path(config['stderr']).write_text('')
                        Path(config['result']).write_text(json.dumps({
                            'termination': 'timeout', 'exit_code': -1,
                            'runtime_seconds': seconds, 'peak_working_set_bytes': 1234,
                        }))
                    return subprocess.CompletedProcess(command, 0, b'', b'')

                def fake_output(command, **kwargs):
                    return b'' if command[1] == 'status' else 'test-commit\n'

                with patch.object(runner, 'ROOT', root), patch.object(runner, 'parse_args', return_value=args), \
                     patch.object(runner, 'win', side_effect=str), \
                     patch.object(runner.subprocess, 'run', side_effect=fake_run), \
                     patch.object(runner.subprocess, 'check_output', side_effect=fake_output), \
                     contextlib.redirect_stdout(io.StringIO()):
                    runner.main()
                out = root/'evidence/verification/runs/test-only'
                run = json.loads((out/'run.json').read_text())
                results = json.loads((out/'results.json').read_text())
                self.assertEqual(run['limits']['per_query_seconds'], seconds)
                self.assertEqual(run['limits']['wrapper_timeout_seconds'], seconds+30)
                self.assertEqual(run['result_count'], 1)
                self.assertEqual(results[0]['status'], 'timeout')
                self.assertIsNone(results[0]['verdict'])
                self.assertEqual(sum('-Config' in c for c, _ in calls), 1)


if __name__ == '__main__':
    unittest.main()
