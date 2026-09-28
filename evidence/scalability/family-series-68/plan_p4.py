#!/usr/bin/env python3
"""Emit a proposed P4 schedule; never execute it or authorize a series."""
import argparse
import json
from pathlib import Path
import query_schema
from run_checks import SEARCH

HERE = Path(__file__).resolve().parent


def plan():
    steps = []
    for repeat in (1, 2, 3):
        steps.append({'repeat': repeat, 'phase': 'generation', 'N': [1, 2, 3, 4],
                      'timeout_seconds': 30, 'command': ['python3', '-B', 'generate.py']})
        for n in (1, 2, 3, 4):
            common = {'repeat': repeat, 'N': n, 'model': f'generated/n{n}/model.xml',
                      'memory_stop_bytes': 2147483648, 'parallelism': 1}
            steps.append({**common, 'phase': 'compile', 'timeout_seconds': 60,
                          'environment': {'UPPAAL_COMPILE_ONLY': '1'},
                          'arguments': [f'generated/n{n}/model.xml']})
            steps.append({**common, 'phase': 'load-and-parse', 'timeout_seconds': 60,
                          'arguments': SEARCH + ['--query-index', '0',
                                        f'generated/n{n}/model.xml', f'generated/n{n}/parse-all.q']})
            for row in query_schema.rows(n):
                steps.append({**common, 'phase': 'model-checking', 'timeout_seconds': 60,
                              'query_id': row['id'], 'formula': row['query'],
                              'query': f'generated/n{n}/{row["path"]}',
                              'arguments': SEARCH + ['-t', '0', '-f', f'<run-directory>/r{repeat}-n{n}-{row["id"]}-trace',
                                            f'generated/n{n}/model.xml', f'generated/n{n}/{row["path"]}']})
    return {'status': 'proposed_not_authorized', 'new_gate_1_required': True,
            'executor': 'future P4 runner; this script emits data only',
            'total_verifier_wall_budget_seconds': 7200,
            'query_runs': sum(s['phase'] == 'model-checking' for s in steps),
            'retry_policy': 'no additional attempts or automatic budget escalation',
            'stop_rules': 'PROTOCOL.md', 'steps': steps}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    data = json.dumps(plan(), indent=2) + '\n'
    if args.output:
        path = args.output.resolve()
        if not path.is_relative_to(HERE):
            parser.error('output must remain within the Issue write scope')
        path.write_text(data)
    else:
        print(data, end='')


if __name__ == '__main__':
    main()
