"""PHY reports must distinguish parsed output from completed verification."""
import copy
import csv
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from uppaal_mcp.config import UppaalConfig
from uppaal_mcp.phy.defaults import build_default_contract
from uppaal_mcp.phy.reports import export_report_bundle, generate_report_bundle
from uppaal_mcp.verifyta import VerifytaRunner


class PhyReportStatusTests(unittest.TestCase):
    def setUp(self):
        self.contract = build_default_contract().to_dict()
        self.properties = self.contract['properties']
        self.queries = [item['query'] for item in self.properties]

    def reports(self, result):
        return generate_report_bundle(contract_json=self.contract, result_json=result)['reports']

    def result(self, status, outcomes):
        return {'status': status, 'query_results': [
            {'formula': query, 'status': outcome}
            for query, outcome in zip(self.queries, outcomes)]}

    def assert_property_states(self, reports, expected):
        rows = list(csv.DictReader(io.StringIO(reports['properties.csv'])))
        self.assertEqual(list(rows[0]), ['name', 'category', 'query', 'result', 'source', 'line'])
        self.assertEqual([row['result'] for row in rows], expected)
        names = {item['name'] for item in self.properties}
        markdown = {}
        for line in reports['report.md'].splitlines():
            if line.startswith('| '):
                cells = line.strip('| ').split(' | ')
                if cells[0] in names:
                    markdown[cells[0]] = cells[3]
        self.assertEqual(markdown, {item['name']: value
                                  for item, value in zip(self.properties, expected)})

    def test_unsuccessful_runs_do_not_publish_partial_verdicts(self):
        for status in ('error', 'timeout', 'tool_not_found', 'validation_failed',
                       'static_only', 'not_verified', 'unknown', 'success', None):
            with self.subTest(status=status):
                reports = self.reports(self.result(status, ['satisfied', 'not_satisfied']))
                self.assert_property_states(reports, ['not_verified'] * len(self.properties))
                self.assertIn('Overall status:', reports['report.md'])
                violations = reports['violations.md']
                self.assertIn('No property verdicts', violations)
                self.assertIn('diagnostic only', violations)
                self.assertIn('satisfied', violations)
                self.assertIn('not_satisfied', violations)
                self.assertNotIn('Suggested fix', violations)
                self.assertNotIn('no failed parsed query', violations)
                self.assertNotIn('No violated property', violations)

    def test_absent_result_is_not_run(self):
        reports = self.reports(None)
        self.assert_property_states(reports, ['not_run'] * len(self.properties))
        self.assertIn('No verification result supplied', reports['report.md'])
        self.assertNotIn('violations.md', reports)

    def test_empty_and_missing_run_status_cannot_establish_results(self):
        for result in ({}, {'query_results': [{'formula': self.queries[0], 'status': 'satisfied'}]}):
            with self.subTest(result=result):
                reports = self.reports(result)
                self.assert_property_states(reports, ['not_verified'] * len(self.properties))
                self.assertIn('No property verdicts', reports['violations.md'])

    def test_completed_mixed_results_preserve_query_outcomes(self):
        for status in ('satisfied', 'not_satisfied', 'inconclusive'):
            with self.subTest(status=status):
                values = ['satisfied', 'not_satisfied', 'maybe', 'inconclusive']
                reports = self.reports(self.result(status, values))
                self.assert_property_states(reports, values + ['not_run'] * (len(self.properties) - 4))
                violations = reports['violations.md']
                self.assertIn('Violated properties', violations)
                self.assertIn('Suggested fix', violations)
                self.assertIn('Queries without a decisive verdict', violations)
                self.assertNotIn('diagnostic only', violations)

    def test_inconclusive_queries_are_not_reported_as_violations(self):
        for outcome in ('maybe', 'inconclusive', 'unknown', None):
            with self.subTest(outcome=outcome):
                reports = self.reports(self.result('inconclusive', [outcome]))
                expected = outcome if outcome in ('maybe', 'inconclusive') else 'not_verified'
                self.assert_property_states(reports, [expected] + ['not_run'] * (len(self.properties) - 1))
                violations = reports['violations.md']
                self.assertIn('Queries without a decisive verdict', violations)
                self.assertNotIn('Suggested fix', violations)
                self.assertNotIn('Violated properties', violations)
                self.assertNotIn('No violated property', violations)

    def test_completed_positive_results_limit_absence_claim_to_returned_queries(self):
        reports = self.reports(self.result('satisfied', ['satisfied']))
        self.assert_property_states(reports, ['satisfied'] + ['not_run'] * (len(self.properties) - 1))
        self.assertIn('among returned query results', reports['violations.md'])

    def test_completed_empty_results_have_no_verdict(self):
        reports = self.reports(self.result('satisfied', []))
        self.assert_property_states(reports, ['not_run'] * len(self.properties))
        self.assertIn('No query results were reported', reports['violations.md'])
        self.assertNotIn('No violated property', reports['violations.md'])

    def test_actual_runner_failure_after_partial_success_stays_diagnostic(self):
        model = '<nta><template><name>P</name><location id="id0"/><init ref="id0"/></template><system>p=P(); system p;</system></nta>'
        stdout = 'Verifying formula 1\n -- Formula is satisfied.\n'
        completed = subprocess.CompletedProcess(['mock-verifyta'], 1, stdout, 'syntax error\n')
        with tempfile.TemporaryDirectory() as directory:
            runner = VerifytaRunner(UppaalConfig('mock-verifyta', Path(directory)))
            with patch('uppaal_mcp.verifyta.subprocess.run', return_value=completed):
                result = runner.verify(model_xml=model, queries='\n'.join(self.queries[:2])).to_dict()
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['query_results'][0]['status'], 'satisfied')
        reports = self.reports(result)
        self.assert_property_states(reports, ['not_verified'] * len(self.properties))
        self.assertIn('diagnostic only', reports['violations.md'])

    def test_actual_runner_timeout_and_complete_controls(self):
        model = '<nta><template><name>P</name><location id="id0"/><init ref="id0"/></template><system>p=P(); system p;</system></nta>'
        stdout = 'Verifying formula 1\n -- Formula is satisfied.\n'
        with tempfile.TemporaryDirectory() as directory:
            runner = VerifytaRunner(UppaalConfig('mock-verifyta', Path(directory)))
            with patch('uppaal_mcp.verifyta.subprocess.run', side_effect=
                       subprocess.TimeoutExpired(['mock-verifyta'], 1, output=stdout.encode())):
                timed_out = runner.verify(model_xml=model, queries=self.queries[0]).to_dict()
            with patch('uppaal_mcp.verifyta.subprocess.run', return_value=
                       subprocess.CompletedProcess(['mock-verifyta'], 0, stdout, '')):
                completed = runner.verify(model_xml=model, queries=self.queries[0]).to_dict()
        self.assertEqual(timed_out['status'], 'timeout')
        self.assert_property_states(self.reports(timed_out), ['not_verified'] * len(self.properties))
        self.assertEqual(completed['status'], 'satisfied')
        self.assert_property_states(self.reports(completed), ['satisfied'] + ['not_run'] * (len(self.properties) - 1))

    def test_export_preserves_results_trace_and_input_objects(self):
        result = self.result('error', ['satisfied', 'not_satisfied'])
        result.update(stdout='partial output', stderr='syntax error', command=['mock-verifyta'])
        original = copy.deepcopy(result)
        contract = copy.deepcopy(self.contract)
        trace = 'State: ObsBeamRecovery.Violation\n'
        with tempfile.TemporaryDirectory() as directory:
            export_report_bundle(directory, contract_json=self.contract, result_json=result, trace_text=trace)
            output = Path(directory)
            self.assertEqual(json.loads((output / 'results.json').read_text(encoding='utf-8')), original)
            self.assertEqual((output / 'trace.txt').read_text(encoding='utf-8'), trace)
            self.assertIn('diagnostic only', (output / 'violations.md').read_text(encoding='utf-8'))
            reports = {name: (output / name).read_text(encoding='utf-8')
                       for name in ('report.md', 'properties.csv')}
            self.assert_property_states(reports, ['not_verified'] * len(self.properties))
        self.assertEqual(result, original)
        self.assertEqual(self.contract, contract)


if __name__ == '__main__':
    unittest.main()
