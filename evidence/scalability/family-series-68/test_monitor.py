#!/usr/bin/env python3
"""Harmless native Windows controls, no verifyta. Run after checkpoint.

Writes immutable raw monitor evidence under checks/<run-id>; proves streaming,
measured-memory stop, time stop and child reaping against Windows PowerShell.
"""
import argparse
import base64
import json
import re
import subprocess

import run_checks as r


def command(script):
    script = "$ProgressPreference='SilentlyContinue'; " + script
    encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    return ['-NoProfile', '-NonInteractive', '-EncodedCommand', encoded]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id', required=True)
    args = ap.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', args.run_id):
        ap.error('simple unique run-id required')
    folder = r.g.HERE / 'checks' / args.run_id
    if folder.exists():
        ap.error('existing evidence is immutable')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=r.g.ROOT, text=True).strip()
    # This test is not a verification claim. Record actual state, including earlier
    # diagnostic artifacts if controls are executed in an ongoing campaign.
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=r.g.ROOT, text=True).strip()
    folder.mkdir(parents=True)
    hardware = r.probe(folder)
    cases = [
        ('normal', "[Console]::Out.Write('sample stdout'); [Console]::Error.Write('sample stderr'); Start-Sleep -Seconds 1", 5, r.MEMORY_BYTES, 'success'),
        ('timeout', 'Start-Sleep -Seconds 10', 1, r.MEMORY_BYTES, 'timeout'),
        # Far below interpreter baseline, so a real measured sample must trigger.
        ('memory', 'Start-Sleep -Seconds 10', 5, 1024 * 1024, 'memory_limit'),
    ]
    report = {'source_commit': commit, 'working_tree_before_test': 'dirty' if dirty else 'clean',
              'kind': 'native monitor controls only, no verifier or model checking',
              'hardware': hardware, 'cases': []}
    for name, script, timeout, memory, expected in cases:
        rec = r.monitor_run(folder, name, r.POWERSHELL, command(script), timeout, memory_bytes=memory)
        checks = {'expected_status': rec['status'] == expected,
                  'measured_private_memory': rec['peak_private_bytes'] > 0,
                  'measured_peak_working_set': rec['peak_reported_working_set_bytes'] > 0,
                  'process_reaped': rec['process_reaped'],
                  'sampled_memory': rec['samples'] > 0,
                  'measured_sample_gap': rec['maximum_sample_gap_seconds'] > 0}
        if name == 'normal':
            checks['stdout_exact'] = (folder / 'normal.stdout.txt').read_bytes() == b'sample stdout'
            checks['stderr_exact'] = (folder / 'normal.stderr.txt').read_bytes() == b'sample stderr'
        elif name == 'memory':
            checks['measured_threshold_crossed'] = max(rec['peak_private_bytes'], rec['peak_reported_working_set_bytes']) >= memory
        report['cases'].append({'name': name, 'expected_status': expected, 'actual_status': rec['status'],
                                 'checks': checks, 'monitor_reference': f'{name}.monitor.json'})
        r.write_json(folder / 'test-report.json', report)
        if not all(checks.values()):
            raise SystemExit(f'Monitor control failed: {name}: {checks}; see raw files')
        print(f'{name}: {expected}, native memory measured, process reaped', flush=True)
    assert r.verdict('-- Formula is satisfied.') == 'satisfied'
    assert r.verdict('-- Formula is NOT satisfied.') == 'violated'
    assert r.verdict('') is None
    assert r.verdict('-- Formula is satisfied.\n-- Formula is satisfied.') is None
    report['verdict_parser_controls'] = 'passed'
    report['all_controls_passed'] = True
    r.write_json(folder / 'test-report.json', report)


if __name__ == '__main__':
    main()
