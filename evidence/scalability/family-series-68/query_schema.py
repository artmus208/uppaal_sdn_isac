"""Compact candidate P4 schema. One external file per measured query."""
import json


def rows(n):
    if type(n) is not int or n not in (1, 2, 3, 4):
        raise ValueError('N must be one of 1,2,3,4')
    assumptions = ['full generated composition; no reduction',
                   'optional service, no fairness or priorities',
                   'abstract time and frozen observer limitations retained']
    result = []

    def add(identifier, query, role, meaning, scope, substitution, nonvacuity, source=None):
        result.append({'id': identifier, 'query': query, 'role': role,
                       'scientific_meaning': meaning, 'claim_scope': scope,
                       'substitution': substitution, 'assumptions': assumptions,
                       'nonvacuity': nonvacuity, 'source_obligation': source,
                       'verdict': None, 'measurement_unit': 'one fresh process, one query',
                       'path': f'p4/{identifier}.q'})

    add('shared-capacity', 'A[] (' + ' + '.join(f'(family_grant_{i} ? 1 : 0)' for i in range(n)) + ' <= 1)',
        'global-safety', 'At most one recorded service opportunity in an epoch; not an ACK or useful departure after overflow.',
        'one global invariant at this N; not an arbitrary-N theorem',
        'sum grant indicators over i=0..N-1',
        [f'u{i}-service' for i in range(n)])
    for i in range(n):
        add(f'u{i}-service', f'E<> family_grant_{i}', 'entity-reachability',
            'Some execution selects this UAV for service. Different UAV witnesses may be different executions; no eventual-service guarantee.',
            f'entity {i} in full N={n} composition', 'one formula for each concrete i=0..N-1',
            ['predicate false initially; witness must traverse shared service epoch'])
    add('joint-backlog', 'E<> ' + ' && '.join(f'u{i}_mac_queue_q > 0' for i in range(n)),
        'global-reachability', 'All encoded queues can be nonzero at the same instant, including absorbing overflow sentinels; N=1 is the nonempty control.',
        'one simultaneous encoded-backlog existential; not necessarily pre-overflow backlog, simultaneous service or sustained congestion',
        'conjunction over i=0..N-1', ['all queues start empty; a witness must include queue arrivals'])
    add('u0-queue-safety', 'A[] !u0_mac_queue_overflow_seen', 'fixed-entity-original-obligation',
        'No sticky overflow witness is ever recorded for u0. Optional service means truth is not presumed.',
        'original C01-queue predicate for fixed entity u0 inside full composition',
        'exact alpha-renaming mac_ -> u0_mac_; predicate size independent of N',
        ['u0-queue-full'], 'C01-queue: A[] !mac_queue_overflow_seen')
    add('family-queue-safety', 'A[] !(' + ' || '.join(f'u{i}_mac_queue_overflow_seen' for i in range(n)) + ')',
        'whole-family-original-obligation', 'Every UAV satisfies the original queue invariant in this same composition.',
        'one query with a growing predicate; kept separate from fixed-u0 cost and an N-query suite',
        'conjunction of N original C01-queue obligations, expressed as negated disjunction',
        ['joint-backlog', 'u0-queue-full; does not establish queue-full reachability for every entity'],
        'C01-queue instantiated for each i; no strengthening of a per-entity predicate')
    add('u0-queue-full', 'E<> u0_mac_queue_q == u0_mac_queue_K && !u0_mac_queue_overflow_seen',
        'nonvacuity', 'u0 can reach capacity K without an earlier overflow; exercises the boundary relevant to C01-queue.',
        'fixed u0; not evidence for all other entities or time divergence',
        'exact alpha-renaming of frozen queue-full diagnostic; K remains 4',
        ['predicate false initially; requires arrivals over multiple epochs'],
        'queue-full: E<> mac_queue_q == mac_queue_K && !mac_queue_overflow_seen')
    return result


def artifacts(n):
    data = rows(n)
    files = {row['path']: (row['query'] + '\n').encode() for row in data}
    files['p4-queries.json'] = (json.dumps(data, indent=2, sort_keys=True) + '\n').encode()
    # The first query alone is executed by --query-index 0 during load/parser checks.
    files['parse-all.q'] = b'E<> true\n' + ''.join(row['query'] + '\n' for row in data).encode()
    return files
