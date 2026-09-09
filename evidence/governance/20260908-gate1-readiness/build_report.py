"""Build auditable proposal/matrix from immutable readiness run and GitHub snapshot."""
import itertools
import json
from pathlib import Path
import re
import subprocess
import yaml
from audit import BASE, HERE, HIST, ROOT, sha, write

RUN = HERE / 'gate1-readiness-001-20260909'
EVIDENCE_COMMIT = '780ba277a78d0962d980a7baf9bcd88867569dc1'


def ref(path, pointer=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    relative = path.relative_to(ROOT).as_posix()
    result = {'path': relative, 'sha256': sha(path.read_bytes()),
              'commit': EVIDENCE_COMMIT if path.is_relative_to(RUN) else BASE}
    if path.is_relative_to(HERE) and not path.is_relative_to(RUN):
        result['commit'] = 'containing_report_commit'
    if pointer:
        result['pointer'] = pointer
    return result


def main():
    composition = json.loads((RUN / 'generated/composition.json').read_bytes())
    comparison = json.loads((RUN / 'comparison.json').read_bytes())
    checks = json.loads((RUN / 'checks.json').read_bytes())
    snapshot = json.loads((HERE / 'github-snapshot.json').read_bytes())
    historical_checks = json.loads((HIST / 'checks.json').read_bytes())
    scopes = []
    for issue in snapshot['open_issues']['issues']:
        match = re.search(r'(?im)^Write scope[^\n]*\n((?:- [^\n]*\n)+)', issue['body'])
        assert match, issue['issue_number']
        scopes.append({'issue': issue['issue_number'], 'reference': issue['url'],
                       'paths': [line[2:] for line in match[1].splitlines()]})
    scopes.append({'issue': 21, 'reference': 'https://github.com/artmus208/uppaal_sdn_isac/issues/21',
                   'paths': [HERE.relative_to(ROOT).as_posix() + '/**']})
    conflicts = []
    for a, b in itertools.combinations(scopes, 2):
        for x, y in itertools.product(a['paths'], b['paths']):
            # All observed scopes are literal paths or trailing /** directories.
            assert '*' not in x.rstrip('*') and '*' not in y.rstrip('*')
            overlap = x == y or (x.endswith('/**') and y.startswith(x[:-2])) or (y.endswith('/**') and x.startswith(y[:-2]))
            if overlap:
                conflicts.append({'issues': [a['issue'], b['issue']], 'paths': [x, y]})
    scope_result = {'captured_at_utc': snapshot['captured_at_utc'], 'source': ref(HERE / 'github-snapshot.json'),
                    'conservative_active_set': 'All open Issues, including in-review historical work, plus #21.',
                    'scopes': scopes, 'conflicts': conflicts,
                    'limitation': 'Snapshot only; recheck live Issues before future freeze or new assignments.'}
    write(HERE / 'scope-audit.json', scope_result)
    assert not conflicts
    source_hash = sha(''.join(f'{v}  {k}\n' for k, v in sorted(composition['source_hashes'].items())).encode())
    formalizations = {k: v for k, v in composition['source_hashes'].items() if k.startswith('levels_tex/')}
    model_source_hash = sha(''.join(f'{v}  {k}\n' for k, v in sorted(formalizations.items())).encode())
    declaration = json.loads((RUN / 'parameter-set.json').read_bytes())
    proposal = {'schema_version': 1, 'kind': 'baseline_proposal_not_manifest',
        'proposed_id': 'reviewer-r1-integrated-single-uav-v1', 'status': 'blocked_pending_independent_decisions',
        'frozen': False, 'gate_1_accepted': False, 'issue': 21,
        'source_commit': BASE, 'execution_commit': composition['source_commit'],
        'evidence_checkpoint': EVIDENCE_COMMIT,
        'supersedes_only_after_future_decision': ref('manifests/baselines/reviewer-r1.yaml'),
        'model': ref(RUN / 'generated/model.xml'), 'query_set': ref(RUN / 'generated/queries.q'),
        'query_count': comparison['query_count'], 'query_map': ref(RUN / 'query-map.json'),
        'parameter_set': declaration, 'parameter_set_artifact': ref(RUN / 'parameter-set.json'),
        'instance_vector': composition['instance_vector'], 'instance_vector_artifact': ref(RUN / 'instance-vector.json'),
        'process_counts': comparison['process_counts'],
        'interface_contract': ref('evidence/instantiation/20260907-p2-scope/interface-contract.md'),
        'interface_implementation_decisions': ref('evidence/instantiation/20260908-p2-integrated/decisions.md'),
        'interface_map': ref(RUN / 'interface-map.json'),
        'generator_hash': composition['generator_hash'], 'implementation_sources': composition['implementation_sources'],
        'generator_hash_construction': composition['generator_hash_construction'],
        'generator_hash_coverage': 'Seven integrated/*.py files, including replay; underlying layer inputs are covered separately by strict source_hashes. Not interchangeable with the historical baseline generator aggregate.',
        'source_hash': source_hash, 'source_hashes': composition['source_hashes'],
        'source_hash_construction': 'SHA256 of UTF-8 records <sha256><two spaces><path><LF>, sorted bytewise by path; all 39 strict inputs, including specification/scientific manifests. This proposed aggregate is not the historical four-TeX source_hash.',
        'model_formalization_hash': model_source_hash, 'model_formalization_files': formalizations,
        'model_formalization_hash_construction': 'Same record format, sorted bytewise, four layer TeX inputs only.',
        'context_document_hashes': composition['context_document_hashes'],
        'manuscript_source': ref('levels_tex/samplepaper.tex'), 'submitted_pdf': ref('pdfs/018100004273.pdf'),
        'manuscript_canonical_selection': 'proposed; explicit selection/build/comparison disposition not demonstrated in inspected inputs',
        'manuscript_build_status': 'not_demonstrated', 'source_pdf_equivalence': 'not_demonstrated',
        'toolchain': {'historical_version_evidence': ref(HIST / 'verifyta-version.stdout.log'),
                     'actual_version_evidence': ref(RUN / 'verifyta-version.stdout.log'),
                     'version': (RUN / 'verifyta-version.stdout.log').read_text().splitlines()[0],
                     'historical_compile_command': next(x for x in historical_checks['commands'] if x['name'] == 'compile-only'),
                     'current_checks': ref(RUN / 'checks.json'),
                     'python_dependencies': ref(RUN / 'pip-freeze.stdout.log'),
                     'model_checking_license_status': 'not_tested',
                     'future_P3_P4_options': 'not_selected; must be recorded in runner contract and per-run evidence after Gate 1'},
        'claim_limits': composition['limitations'] + [
            'No physical time scale or empirical calibration; no executed simulator adapter.',
            '81 queries have IDs and exact bytes, not accepted scientific coverage or verdicts.',
            'No numeric packet-queue capacity or recovery-attempt bound; no reinterpretation of policy counters as packet/retry counts.',
            'Service completion at 40 is an event, not a global experiment horizon or proof of time divergence.',
            'Historical vector status/source_commit describes the input specification; retained verbatim, not current implementation status.'],
        'independent_decision_references': [], 'verification_status': 'not_run'}
    write(HERE / 'proposed-baseline.json', proposal)
    rows = []
    github = ref(HERE / 'github-snapshot.json')
    def row(requirement, status, evidence, finding, role, next_action, decision=None, origin='manifests/collaboration-v1.yaml#gates.gate_1.requires'):
        rows.append({'requirement': requirement, 'requirement_source': origin, 'status': status,
                     'evidence': evidence, 'independent_decision_reference': decision,
                     'finding': finding, 'required_role': role, 'next_action': next_action})
    row('P0_candidate_exists', 'ready', [ref('manifests/baselines/reviewer-r1.yaml'), github],
        'Historical candidate exists in merged read; #6 authorizes preservation/supersession procedure only.',
        'Independent Integrator', 'Retain historical candidate when selecting its reviewed successor.',
        'https://github.com/artmus208/uppaal_sdn_isac/issues/6#issuecomment-5572059620')
    row('P1_parameter_decisions_accepted', 'blocked', [github, ref('evidence/validation/20260907-p1/validation-report.md'), ref(RUN / 'parameter-set.json')],
        'Issue #15 has no comments; PR #16 has no reviews/discussion decisions. Method and abstract values are supplied, acceptance is absent.',
        'Independent P1 scientific reviewer / Integrator', 'Record whether abstract units/bounds and calibration-method-only claims suffice; accept or reject exact P1 package and chosen parameter set in #15.')
    row('P2_integrated_model_accepted', 'blocked', [github, ref('evidence/instantiation/20260907-p2-scope/decisions.md'), ref('evidence/instantiation/20260908-p2-integrated/decisions.md')],
        'Merged #18/#20 and successful software checks do not supply a scientific decision; reviews/discussion timelines are empty and #19 comments only hand off candidate evidence.',
        'Independent P2 scientific reviewer / Integrator', 'Accept/reject specification #17 and implementation #19 with explicit dispositions for the semantic questions in decision-proposal.md.')
    row('integrated_model_present', 'ready', [ref(RUN / 'generated/model.xml'), ref(RUN / 'comparison.json')],
        'Exact regenerated integrated XML contains 50 processes: 20 core, eight boundary and 22 observers; bytes equal merged PR #20.',
        'Independent P2 reviewer', 'Use these exact bytes as the candidate under review; scientific acceptance is tracked separately.')
    row('interface_contract_accepted', 'blocked', [github, ref('evidence/instantiation/20260907-p2-scope/interface-contract.md'), ref(RUN / 'interface-map.json')],
        'Proposed contract and implementation maps exist; no independent acceptance of ownership, mappings, staging, age or event semantics is recorded.',
        'Independent P2 reviewer', 'Explicitly accept or require corrections to interface-contract.md plus implemented adaptations; review policy/location ambiguity, admission and observer semantics.')
    row('model_query_parameter_and_instance_hashes_pinned', 'blocked', [ref(HERE / 'proposed-baseline.json'), ref(RUN / 'comparison.json'), ref('manifests/baselines/reviewer-r1.yaml')],
        'All candidate byte hashes/maps are available, but the active historical manifest has null canonical sets and no integrated-model pin; proposal is not an accepted successor.',
        'Coordinator with independent Integrator decision', 'After science/license decisions, create separate manifest-specific supersession Issue; freeze accepted hashes without rewriting historical evidence.')
    row('static_validation_passed', 'ready', [ref(RUN / 'checks.json'), ref(RUN / 'comparison.json'), ref(HIST / 'checks.json')],
        'Fresh generation, XML/location/query references, all metadata except execution commit, 47 source files, 113 historical checksums and original static audit agree; 147 software tests exit 0. Historical real compile-only exit 0 applies to identical XML/query bytes.',
        'Independent evidence reviewer', 'Audit recorded raw logs and reproduce in a new directory; do not turn static results into property verdicts.')
    row('working_verifyta_and_license_confirmed', 'not-demonstrated', [ref(RUN / 'verifyta-version.stdout.log'), ref(HIST / 'summary.json'), ref(HIST / 'checks.json')],
        'Real version exits 0; historical compile-only exits 0. Both runs explicitly lack a model-checking license probe, so present license availability is unknown.',
        'Authorized Runner, reviewed by independent Integrator', 'Create a separate narrowly scoped runner contract for a minimal licensing smoke, with exact model/query/command, environment and claim limits; execute only under that contract.')
    row('active_write_scopes_do_not_overlap', 'ready', [ref(HERE / 'scope-audit.json'), github],
        'No pair overlaps among the conservatively treated ten open Issues plus #21, at recorded capture time.',
        'Coordinator', 'Recheck active scopes before new assignments and freeze; scope of #6 includes shared manifest paths and requires coordination before a successor Issue.')
    extra = 'manifests/v1.md#4-P0-Baseline; CONTRIBUTING.md#10-Gates'
    row('canonical_manuscript_source_and_hash', 'blocked', [ref('levels_tex/samplepaper.tex'), ref('pdfs/018100004273.pdf'), ref('manifests/baselines/reviewer-r1.yaml')],
        'Source and PDF exact hashes recorded, but inspected inputs provide no explicit successor canonical-source selection or build/PDF-comparison disposition. No equivalence or mismatch inferred.',
        'Independent Integrator / manuscript owner', 'Select canonical source and record build status plus PDF comparison result or explicit unresolved disposition in the successor baseline; manuscript edits, if needed, belong to P9a/P9b.', origin=extra)
    row('source_generator_hashes_and_clean_provenance', 'ready', [ref(RUN / 'comparison.json'), ref(HERE / 'proposed-baseline.json')],
        'All 39 strict inputs, seven implementation files and operational AGENTS bytes equal base Git blobs; source and generator aggregate constructions are explicit and distinct from historical definitions.',
        'Independent Integrator', 'Approve the hash constructions and exact selected bytes before inserting them in a successor manifest.', origin=extra)
    row('query_ids_and_scientific_coverage', 'blocked', [ref(RUN / 'query-map.json'), ref('evidence/validation/20260907-p1/validation-report.md')],
        '81 unique query IDs, no excluded source query, and valid process/location references. Coverage acceptance is absent: finite queue/resource labels are not numerical queue/retry bounds required by C01; modified observers need claim review.',
        'Independent scientific reviewer with P1/P2 owners', 'Map accepted candidate queries to intended C01/C02 claims and explicitly resolve absent numeric queue/retry semantics before freezing; no P3 work starts here.', origin=extra)
    row('tool_version_and_execution_parameters_recorded', 'ready', [ref(RUN / 'checks.json'), ref(RUN / 'verifyta-version.stdout.log'), ref(HIST / 'checks.json')],
        'Current version and exact audit commands/overrides are saved; historical compile-only command/flag is pinned. Future model-checking options remain unselected, explicitly so.',
        'Runner / Coordinator', 'Select and record later model-checking options and per-run resource limits under the appropriate contract after Gate 1; version success does not resolve license row.', origin=extra)
    row('independent_gate_record_commit_time_owner', 'blocked', [github, ref('manifests/baselines/reviewer-r1.yaml')],
        'No accepted Gate 1 decision exists in inspected references; historical gate is pending/frozen:false. #6 decision authorizes procedure only.',
        'Independent Integrator and Gate 1 coordinator', 'After every blocker is resolved, record accepted/rejected with exact commit, timestamp, reviewer identity, source/generator/model/query hashes, parameter set and vector in a separate governance Issue.', origin=extra)
    required = yaml.safe_load((ROOT / 'manifests/collaboration-v1.yaml').read_text())['gates']['gate_1']['requires']
    assert set(required).issubset({x['requirement'] for x in rows})
    matrix = {'schema_version': 1, 'issue': 21, 'base_commit': BASE,
              'snapshot_at_utc': snapshot['captured_at_utc'], 'overall_readiness': 'blocked',
              'status_definitions': {'ready': 'Artifact/check demonstrated for this row only; not scientific acceptance.',
                                     'blocked': 'Known required decision or accepted pin is missing.',
                                     'not-demonstrated': 'Required capability has no qualifying evidence; neither success nor present failure inferred.'},
              'rows': rows, 'verification_status': 'not_run', 'gate_1_accepted': False}
    write(HERE / 'readiness-matrix.json', matrix)
    print(json.dumps({'requirements': len(rows), 'statuses': {s: sum(r['status'] == s for r in rows) for s in ('ready', 'blocked', 'not-demonstrated')}, 'overlapping_scopes': len(conflicts)}))


if __name__ == '__main__':
    main()
