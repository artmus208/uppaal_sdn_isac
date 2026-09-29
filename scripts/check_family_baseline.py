"""Audit the finite UAV family; never authorize activation or verifier execution.

The manifest uses the JSON subset of YAML so this audit needs only stdlib.
The historical single-model auditor and current.json retain their old meaning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'manifests/baselines/uav-family-r1.yaml'
PACKET = 'evidence/governance/family-gate1-20260929/'
HEAD = 'c439b0811c8f0063ee44e968587d08a46361b4b4'
BASE = '939ccbcba8d6d3381eb4c4288a0cd6de432dfd2d'
DECISION = 'https://github.com/artmus208/uppaal_sdn_isac/pull/73#issuecomment-5890790922'
HISTORICAL = 'manifests/baselines/reviewer-r1.yaml'
CONTRACT = 'manifests/collaboration-v2.yaml'
PINNED = {
    'baseline-candidate.json': '6f6ae3a4db4b56d2e6192631971f85b601b72f1441a6ddb9876dc6c47defd4db',
    'input-hashes.json': '4a080b95ad7812e64385eda72e7311f50435fac2b5574f677c85fd902c1ec6a6',
    'query-dispositions.json': '78e721c774d238be34bf935cbc3f6f00cd29fcfe47c61596093954d21db3b654',
}
SELECTION_BLOCK = '''family_baseline_selection:
  manifest: manifests/baselines/uav-family-r1.yaml
  baseline_id: uav-family-r1-20260929
  eligible_workstream: P4
  historical_default: manifests/baselines/reviewer-r1.yaml
  input_scope_decision: https://github.com/artmus208/uppaal_sdn_isac/pull/73#issuecomment-5890790922
  activation_issue: https://github.com/artmus208/uppaal_sdn_isac/issues/74
  activation_rule: Independent Integrator acceptance, merge into read, then decision with exact merge commit and UTC time.
  selection_rule: P4 Issue explicitly pins baseline ID, manifest SHA256, source commit and activation decision; no implicit default change.
  gate_rule: For an explicitly selected family, use its scoped input decision and operational activation record; the historical gate decision_source remains the default only.
  audit_command: python3 scripts/check_family_baseline.py
  automatic_P3_transfer: false
  execution_authorized_by_selection: false
'''


def read(root: Path, relative: str) -> bytes:
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('invalid repository path')
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or p.as_posix() != relative:
        raise ValueError('invalid repository path')
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('path escapes repository')
    return target.read_bytes()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(raw: bytes) -> object:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def packet(root: Path) -> dict:
    result = {}
    for name, expected in PINNED.items():
        raw = read(root, PACKET + name)
        if digest(raw) != expected:
            raise ValueError('accepted packet drift: ' + name)
        result[name] = load_json(raw)
    return result


def expected_manifest(root: Path) -> dict:
    p = packet(root)
    candidate = p['baseline-candidate.json']
    return {
        'schema_version': 'uav-family-1',
        'kind': 'finite-family-input-baseline',
        'metadata': {'id': 'uav-family-r1-20260929',
                     'status': 'frozen_inputs_pending_operational_activation',
                     'frozen': True, 'issue': 74},
        'provenance': {'base_ref': 'read', 'base_commit': BASE,
                       'reviewed_package_commit': HEAD,
                       'model_candidate_commit': candidate['model_candidate_commit'],
                       'input_snapshot_commit': candidate['base_commit']},
        'input_scope_acceptance': {'A': 'accepted', 'B': 'accepted',
                                  'P1_P2_applicability': 'accepted_in_limited_abstract_scope',
                                  'decision_actor': 'user/integrator',
                                  'recorded_by': 'vadimnbkg', 'decision_reference': DECISION},
        'operational_activation': {
            'record_in_issue': 'https://github.com/artmus208/uppaal_sdn_isac/issues/74',
            'requires': ['independent_integrator_acceptance', 'activation_PR_merged_into_read',
                         'decision_with_exact_merge_commit_and_UTC_time'],
            'inclusion_in_a_branch_is_activation': False,
            'P4_execution_authorized': False},
        'selection': {'eligible_workstream': 'P4', 'explicit_issue_selection_required': True,
                      'historical_default': HISTORICAL, 'automatic_P3_transfer': False},
        'claim_scope': {'permitted': 'verifier_attempt_costs_on_exact_finite_inputs',
                        'completed_and_censored_separate': True,
                        'service_reachability': 'open',
                        'does_not_close': ['R03', 'R04', 'C06'],
                        'excluded': ['physical_calibration', 'empirical_validation',
                                     'working_network_scalability', 'useful_throughput',
                                     'centralized_controller_capacity', 'fairness', 'SLA',
                                     'universal_queue_safety', 'whole_system_timed_equivalence']},
        'family_domain': candidate['family_domain'],
        'models': candidate['models'],
        'tool_version': candidate['tool_version'],
        'accepted_packet': {name: {'path': PACKET + name, 'sha256': sha}
                            for name, sha in PINNED.items()},
        'historical_context_only': [CONTRACT],
        'input_hashes': p['input-hashes.json']['files'],
    }


def audit(root: Path = ROOT, audit_history: bool = False) -> dict:
    root = root.resolve()
    expected = expected_manifest(root)
    raw = read(root, MANIFEST)
    actual = load_json(raw)
    # Exact accepted schema: extra fields cannot silently broaden a claim or select a baseline.
    if json.dumps(actual, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError('family manifest differs from accepted input scope/schema')
    config = load_json(read(root, 'manifests/current.json'))
    if config['baseline_manifest'] != HISTORICAL or config['collaboration_manifest'] != CONTRACT:
        raise ValueError('historical default or operational contract was switched')
    contract = read(root, CONTRACT).decode()
    if contract.count('family_baseline_selection:') != 1 or SELECTION_BLOCK not in contract:
        raise ValueError('missing or changed explicit family selection policy')
    current_checks = 0
    history_checks = 0
    for path, sha in actual['input_hashes'].items():
        # Only the operational contract changes here. Its accepted historical bytes
        # remain pinned to the old commit, never compared to its new operational text.
        if path not in actual['historical_context_only']:
            if digest(read(root, path)) != sha:
                raise ValueError('input hash mismatch: ' + path)
            current_checks += 1
        if audit_history:
            raw_input = subprocess.check_output(
                ['git', 'show', actual['provenance']['input_snapshot_commit'] + ':' + path],
                cwd=root, stderr=subprocess.PIPE)
            if digest(raw_input) != sha:
                raise ValueError('historical snapshot hash mismatch: ' + path)
            history_checks += 1
    return {'kind': 'static_validation_not_model_checking',
            'manifest_sha256': digest(raw), 'models': len(actual['models']),
            'queries': len(packet(root)['query-dispositions.json']),
            'current_input_hashes_checked': current_checks,
            'historical_input_hashes_checked': history_checks,
            'activation_checked': False, 'P4_execution_authorized': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-history', action='store_true',
                        help='Also read exact original Git blobs; requires original commit history')
    args = parser.parse_args()
    try:
        print(json.dumps(audit(audit_history=args.audit_history), indent=2))
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print('Family audit failed: ' + str(exc))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
