from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from uppaal_mcp.layers import available_layer_adapters
from uppaal_mcp.sdn.alpha import check_no_continuous_guards, default_profile, validate_threshold_policy
from uppaal_mcp.sdn.benchmarks import generate_benchmark_model, validate_all_benchmarks
from uppaal_mcp.sdn.extractor import extract_contract_model
from uppaal_mcp.sdn.generator import generate_uppaal_model
from uppaal_mcp.sdn.ir import SdnContractModel
from uppaal_mcp.sdn.layout import validate_generated_layout
from uppaal_mcp.sdn.property_pack import generate_property_pack
from uppaal_mcp.sdn.reports import generate_report_bundle
from uppaal_mcp.sdn.tools import generate_uppaal_from_contract, verify_property_pack
from uppaal_mcp.sdn.validators import validate_contract_ir, validate_generated_model
from uppaal_mcp.validation import validate_model_text


ROOT = Path(__file__).resolve().parents[1]
SDN_TEX = ROOT / "levels_tex" / "SDN_RIC_control_plane_formalization.tex"


class SdnLayerTests(unittest.TestCase):
    def test_extract_contract_from_article(self) -> None:
        contract = extract_contract_model(SDN_TEX.read_text(encoding="utf-8"), source_name=SDN_TEX.name)
        self.assertTrue(contract["extractor"]["ok"], contract["extractor"]["diagnostics"])
        self.assertEqual(contract["sdn_components"], ["A_MON", "A_RISK", "A_POLICY", "A_RULE", "A_REC", "A_SDN_AGG"])
        self.assertEqual(contract["env_components"], ["A_ENV_SDN"])
        self.assertIn("A_SDN", contract["extractor"]["compositions"])
        self.assertIn("POL_REJECT", contract["extractor"]["policies_found"])
        self.assertIn("service_admission", contract["extractor"]["interfaces_found"])

    def test_contract_validation(self) -> None:
        contract = SdnContractModel.from_dict(extract_contract_model(SDN_TEX.read_text(encoding="utf-8")))
        report = validate_contract_ir(contract)
        self.assertTrue(report.ok, report.errors)

    def test_generated_model_validates_static_and_generic(self) -> None:
        generated = generate_uppaal_model()
        semantic = validate_generated_model(generated.model_xml, generated.queries)
        self.assertTrue(semantic.ok, semantic.errors)
        generic = validate_model_text(generated.model_xml, generated.queries)
        self.assertTrue(generic.ok, generic.errors)
        self.assertIn("Template_A_POLICY", generic.templates)
        self.assertIn("A[] not ObsRuleMiss.Violation", generic.queries)

    def test_generation_modes(self) -> None:
        minimal = generate_uppaal_from_contract(tex_path=str(SDN_TEX), mode="minimal")
        self.assertTrue(minimal["semantic_validation"]["ok"], minimal["semantic_validation"]["errors"])
        self.assertNotIn("Template_ObsRuleMiss", minimal["model_xml"])
        open_system = generate_uppaal_from_contract(tex_path=str(SDN_TEX), mode="open_system")
        self.assertTrue(open_system["semantic_validation"]["ok"], open_system["semantic_validation"]["errors"])
        self.assertNotIn("A_ENV_SDN = Template_A_ENV_SDN();", open_system["model_xml"])
        self.assertNotIn("A[] not deadlock", open_system["queries"])
        optional_sec = generate_uppaal_from_contract(tex_path=str(SDN_TEX), mode="with_optional_sec")
        self.assertTrue(optional_sec["semantic_validation"]["ok"], optional_sec["semantic_validation"]["errors"])
        self.assertIn("Template_A_SEC", optional_sec["model_xml"])

    def test_alpha_profile_and_raw_guard_rejection(self) -> None:
        self.assertTrue(validate_threshold_policy(default_profile()).ok)
        generated = generate_uppaal_model()
        self.assertTrue(check_no_continuous_guards(generated.model_xml).ok)
        self.assertFalse(check_no_continuous_guards('<label kind="guard">raw_delay &gt; 5</label>').ok)

    def test_property_pack_and_static_verify(self) -> None:
        generated = generate_uppaal_model()
        pack = generate_property_pack(model_xml=generated.model_xml, include_negative=True)
        self.assertIn("negative_property_pack", pack)
        self.assertIn("stale_telemetry", pack["static_checks"])
        result = verify_property_pack(model_xml=generated.model_xml, queries=generated.queries, static_only=True)
        self.assertEqual(result["status"], "validated")

    def test_reports_include_interface_artifacts(self) -> None:
        generated = generate_uppaal_model()
        reports = generate_report_bundle(contract_json=generated.contract, model_xml=generated.model_xml, queries=generated.queries)
        self.assertIn("interface_report.md", reports["reports"])
        self.assertIn("interface_map.md", reports["reports"])

    def test_readable_layout_has_separated_labels_and_loop_lanes(self) -> None:
        generated = generate_uppaal_model(layout="readable")
        report = validate_generated_layout(generated.model_xml)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(report.warnings, [])
        root = ET.fromstring(generated.model_xml)
        for template in root.findall("template"):
            for transition in template.findall("transition"):
                label_points = [
                    (label.attrib["x"], label.attrib["y"])
                    for label in transition.findall("label")
                    if "x" in label.attrib and "y" in label.attrib
                ]
                self.assertEqual(len(label_points), len(set(label_points)))
                source = transition.find("source")
                target = transition.find("target")
                if source is not None and target is not None and source.attrib.get("ref") == target.attrib.get("ref"):
                    self.assertTrue(transition.findall("nail"))

    def test_benchmark_suite_positive_and_broken(self) -> None:
        result = validate_all_benchmarks()
        self.assertTrue(result["ok"], result["results"])
        broken = generate_benchmark_model("broken_stale_optimistic_reconfig")
        self.assertFalse(broken["validation"]["ok"])
        self.assertIn("optimistic_reconfig", ";".join(broken["validation"]["errors"]))

    def test_layer_adapter_registry_contains_sdn(self) -> None:
        adapters = available_layer_adapters()
        self.assertIn("sdn", adapters)
        self.assertEqual(adapters["sdn"].source_name, "SDN_RIC_control_plane_formalization.tex")

    def test_article_golden_fixtures(self) -> None:
        readable = generate_uppaal_from_contract(tex_path=str(SDN_TEX), layout="readable")
        compact = generate_uppaal_from_contract(tex_path=str(SDN_TEX), layout="compact")
        self.assertEqual(readable["model_xml"], (ROOT / "tests/fixtures/sdn_model_article.readable.golden.xml").read_text(encoding="utf-8"))
        self.assertEqual(compact["model_xml"], (ROOT / "tests/fixtures/sdn_model_article.golden.xml").read_text(encoding="utf-8"))
        self.assertEqual(readable["queries"], (ROOT / "tests/fixtures/sdn_queries_article.golden.q").read_text(encoding="utf-8"))


class IntegratedCandidateTests(unittest.TestCase):
    """Concrete XML edge regressions; these are not temporal verification claims."""

    @classmethod
    def setUpClass(cls):
        from uppaal_mcp.integrated.generator import generate
        cls.candidate = generate(ROOT)
        cls.xml = ET.fromstring(cls.candidate.model_xml)

    def replay(self, *processes, **values):
        from uppaal_mcp.integrated.replay import Replay
        return Replay(self.candidate.model_xml, values, processes=processes)

    def move(self, replay, process, state):
        from uppaal_mcp.integrated.xmlutil import loc_id
        replay.locations[process] = loc_id(replay.processes[process], state)

    def step(self, replay, process, *, sync=None, target=None, select=None):
        choices = replay.candidates(process, sync=sync, target=target, select=select)
        self.assertEqual(len(choices), 1, (process, replay.state(process), sync, target))
        replay.take([(process, choices[0], select or {})])
        return choices[0]

    def test_integrated_determinism_and_partition(self):
        from uppaal_mcp.integrated.generator import generate
        second = generate(ROOT)
        self.assertEqual(self.candidate, second)
        order = self.candidate.metadata['system_order']
        self.assertEqual(len(order), 50)
        self.assertEqual(len(set(order)), 50)
        self.assertEqual(sum(p.startswith('obs_') for p in order), 22)
        self.assertEqual(sum(p.startswith('boundary_') for p in order), 8)
        names = [t.findtext('name') for t in self.xml.findall('template')]
        self.assertFalse(any('STUB' in n or 'ENV_' in n for n in names))
        for name in ('app_A_CRIT', 'app_A_SVC_AGG'):
            t = next(t for t in self.xml.findall('template') if t.findtext('name') == name)
            self.assertEqual(len(t.findall('transition')), 0)

    def test_integrated_rejects_changed_source_and_specification(self):
        from unittest.mock import patch
        from uppaal_mcp.integrated.generator import generate
        original = Path.read_bytes
        for suffix in ('phy/defaults.py', 'instance-vector.json'):
            def changed(path, suffix=suffix):
                raw = original(path)
                return raw + b'\n' if path.as_posix().endswith(suffix) else raw
            with self.subTest(suffix=suffix), patch.object(Path, 'read_bytes', changed):
                with self.assertRaises(ValueError):
                    generate(ROOT)

    def test_integrated_identifier_tokens_preserve_shadowing_and_members(self):
        from uppaal_mcp.integrated.xmlutil import rename
        self.assertEqual(rename('int x; int f(int x) { return x; } // x\n"x"', 'mac_'),
                         'int mac_x; int mac_f(int mac_x) { return mac_x; } // x\n"x"')
        self.assertEqual(rename('x1 + x + P.Idle', 'p_', {'P': 'component_0'}),
                         'p_x1 + p_x + component_0.Idle')
        self.assertEqual(rename('i:int[0,2]', 'p_'), 'p_i:int[0,2]')
        decl = self.xml.findtext('declaration')
        self.assertIn('phy_c_rec', decl)
        self.assertIn('sdn_c_rec', decl)

    def test_integrated_ack_endpoints_are_distinct(self):
        channels = self.candidate.metadata['channels']
        expected = {'bus_rule_ack': 'sdn_A_RULE_0', 'bus_ctrl_ack': 'sdn_A_SDN_AGG_0',
                    'bus_rec_policy_ack': 'sdn_A_REC_0', 'bus_rec_flow_ack': 'sdn_A_REC_0',
                    'bus_rec_rollback_ack': 'sdn_A_REC_0'}
        for name, receiver in expected.items():
            self.assertEqual(channels[name]['kind'], 'binary')
            self.assertEqual(channels[name]['receivers'], [receiver])
            self.assertEqual(len(channels[name]['senders']), 1)
        self.assertEqual(channels['sdn_ack']['receivers'], [])

    def test_integrated_joint_schedule_requires_both_deliveries(self):
        bridge = 'boundary_B_PHY_MAC_0'
        r = self.replay(bridge, mac_scheduleMode=3, mac_phy_command_pending=True, bus_schedule_open=True)
        self.step(r, bridge, sync='mac_mac_schedule_cmd?')
        self.assertEqual(r.candidates(bridge, sync='mac_phy_ack!'), [])
        self.step(r, bridge, sync='phy_waveform_config!')
        self.assertEqual(r.candidates(bridge, sync='mac_phy_ack!'), [])
        self.step(r, bridge, sync='phy_sensing_mode_cmd!')
        self.step(r, bridge, sync='mac_phy_ack!')
        self.assertEqual(r.state(bridge), 'Drain')
        self.assertFalse(r.values['bus_schedule_loss'])

    def test_integrated_missing_phy_receiver_records_loss_and_no_ack(self):
        bridge = 'boundary_B_PHY_MAC_0'
        r = self.replay(bridge, mac_scheduleMode=3, mac_phy_command_pending=True, bus_schedule_open=True)
        self.step(r, bridge, sync='mac_mac_schedule_cmd?')
        self.step(r, bridge, sync='phy_waveform_config!')
        r.advance(1)
        self.step(r, bridge, sync='', target='Drain')
        self.assertTrue(r.values['bus_schedule_loss'])
        self.assertEqual(r.candidates(bridge, sync='mac_phy_ack!'), [])
        self.assertEqual(r.candidates(bridge, target='Idle'), [])
        r.values['mac_phy_command_pending'] = False
        r.values['bus_schedule_open'] = False
        self.step(r, bridge, target='Idle')

    def test_integrated_no_late_ack_or_idle_schedule_success(self):
        bridge = 'boundary_B_PHY_MAC_0'
        for mode,pending,clock in [(0,True,0),(1,False,0),(1,True,4)]:
            with self.subTest(mode=mode,pending=pending,clock=clock):
                r = self.replay(bridge,mac_scheduleMode=mode,mac_phy_command_pending=pending,mac_c_phy_ack=clock)
                self.step(r,bridge,sync='mac_mac_schedule_cmd?')
                if mode:
                    self.step(r,bridge,sync='phy_waveform_config!')
                    self.assertEqual(r.candidates(bridge,sync='mac_phy_ack!'),[])
                else:
                    self.step(r,bridge,sync='',target='Drain')
                    self.assertTrue(r.values['bus_schedule_loss'])

    def test_integrated_policy_payload_precedes_mac_receiver(self):
        bridge,mac = 'boundary_B_POLICY_0','mac_A_SCH_0'
        for policy,expected in [(0,(True,True)),(1,(False,True)),(2,(True,False)),
                                (3,(False,False)),(4,(True,True)),(5,(False,False))]:
            r=self.replay(bridge,mac,sdn_policyClass=policy,sdn_command_pending=True)
            self.step(r,bridge,sync='bus_ctrl_request?')
            with self.assertRaises(ValueError):r.advance(0.1)
            self.step(r,bridge,target='Offer')
            a=r.candidates(bridge,sync='bus_policy!')[0]
            b=r.candidates(mac,sync='bus_policy?')[0]
            r.take([(bridge,a,{}),(mac,b,{})])
            self.assertEqual((r.values['mac_sdn_comm_priority_allowed'],r.values['mac_sdn_sensing_priority_allowed']),expected)
            self.assertEqual(r.candidates(bridge,sync='bus_rec_policy_ack!'),[])
            self.step(r,bridge,sync='bus_ctrl_ack!')

    def test_integrated_admission_stages_fields_before_receiver_guard(self):
        bridge,app='boundary_B_ADMISSION_0','app_Req_0'
        r=self.replay(bridge,app,app_service_request_pending=True,app_admissionClass=0,
                      sdn_service_request_pending=True)
        self.move(r,bridge,'AwaitOutcome');self.move(r,app,'RequestPending')
        self.assertEqual(r.candidates(app,sync='app_service_accept?'),[])
        self.step(r,bridge,sync='sdn_service_accept?')
        self.assertEqual(r.values['app_admissionClass'],0)
        self.step(r,bridge,target='Safety')
        self.assertEqual(r.values['app_admissionClass'],1)
        self.step(r,bridge,target='OfferOutcome')
        r.take([(bridge,r.candidates(bridge,sync='app_service_accept!')[0],{}),
                (app,r.candidates(app,sync='app_service_accept?')[0],{})])
        self.assertEqual(r.state(app),'Accepted')
        self.assertFalse(r.values['app_service_request_pending'])

    def test_integrated_unresolved_app_admission_has_real_timeout(self):
        app='app_Req_0'
        r=self.replay(app,app_service_request_pending=True)
        self.move(r,app,'RequestPending')
        r.advance(r.values['app_D_admission'])
        self.step(r,app,sync='',target='Rejected')
        self.assertTrue(r.values['bus_admission_timeout'])
        self.assertFalse(r.values['app_service_request_pending'])
        r.advance(1)

    def test_integrated_duplicate_schedule_does_not_overwrite_mailbox(self):
        bridge='boundary_B_PHY_MAC_0'
        r=self.replay(bridge,mac_scheduleMode=3)
        self.step(r,bridge,sync='mac_mac_schedule_cmd?')
        r.values['mac_scheduleMode']=1
        self.step(r,bridge,sync='mac_mac_schedule_cmd?')
        self.assertEqual(r.locals[bridge]['mode'],3)
        self.assertTrue(r.values['bus_protocol_error'])

    def test_integrated_monitor_counters_are_finite_latches(self):
        decl=self.xml.findtext('declaration')
        self.assertNotRegex(decl,r'int app_\w+_seq\s*=')
        self.assertNotRegex(decl,r'app_\w+_seq\s*\+\s*1')
        self.assertEqual(decl.count('void raise_app_'),8)
        for t in self.xml.findall('template'):
            if t.findtext('name').startswith('app_Obs'):
                self.assertNotIn('app_seen',ET.tostring(t,encoding='unicode'))

    def test_integrated_kpi_age_includes_transport_delay_and_bad_quality(self):
        bridge='boundary_B_KPI_0'
        for age,expected in [(4.99,0),(5,1),(9.99,1),(10,2)]:
            r=self.replay(bridge,bus_phy_age=age,bus_phy_valid=True,bus_phy_pending=True,
                          bus_pd=2,bus_fa=1,bus_miss=1)
            self.move(r,bridge,'Map')
            self.step(r,bridge,target='Mac')
            self.assertEqual(r.values['app_detectionFreshnessClass'],expected)
            self.assertEqual(r.values['mac_kpiFreshnessClass'],expected)
            self.assertEqual(r.values['app_pdClass'],2)
            self.assertEqual(r.values['app_falseAlarmClass'],1)
            self.assertEqual(r.values['bus_phy_age'],age)

    def test_integrated_kpi_deadline_prevents_unrecorded_indefinite_wait(self):
        bridge='boundary_B_KPI_0'
        r=self.replay(bridge,bus_phy_valid=True,bus_phy_pending=True)
        r.advance(1)
        with self.assertRaises(ValueError):r.advance(0.1)
        candidates=r.candidates(bridge,sync='',target='Expired')
        from uppaal_mcp.integrated.xmlutil import label
        drop=next(tr for tr in candidates if 'bus_phy_loss=true' in label(tr,'assignment'))
        r.take([(bridge,drop,{})])
        self.assertTrue(r.values['bus_phy_loss'])
        self.assertFalse(r.values['bus_phy_pending'])

    def test_integrated_sampling_stages_private_values_before_publication(self):
        bridge='boundary_E_PHY_INPUT_0'
        r=self.replay(bridge,phy_SINRClass=2)
        r.advance(5)
        self.step(r,bridge,target='Sample0')
        self.step(r,bridge,target='Sample1',select={'value':0})
        self.assertEqual(r.values['phy_SINRClass'],2)
        with self.assertRaises(ValueError):r.advance(0.1)

    def test_integrated_replay_rejects_unsupported_expressions(self):
        from uppaal_mcp.integrated.replay import expression
        with self.assertRaises(ValueError):expression('x.__class__',{'x':1})

    def test_integrated_admission_request_payload_is_complete(self):
        bridge='boundary_B_ADMISSION_0'
        r=self.replay(bridge,app_serviceClass=4,app_criticalityClass=3,app_pdMinClass=2,
                      app_pfaMaxClass=1,app_coverageBoundClass=2)
        self.step(r,bridge,sync='app_service_request?')
        self.assertEqual(r.values['bus_request_service'],4)
        self.assertEqual(r.values['bus_request_criticality'],3)
        self.assertEqual(r.values['bus_request_pd'],2)
        self.assertEqual(r.values['bus_request_fa'],1)
        self.assertEqual(r.values['bus_request_coverage'],2)

    def test_integrated_query_process_references_exist(self):
        import re
        refs=re.findall(r'\b(\w+)\.(\w+)',self.candidate.queries)
        r=self.replay(*self.candidate.metadata['system_order'])
        for p,name in refs:
            self.assertIn(p,r.processes)
            self.assertIn(name,[x.findtext('name') for x in r.processes[p].findall('location')])


class IntegratedRecorderTests(unittest.TestCase):
    def test_symlinked_venv_preserves_interpreter_and_cli(self):
        import contextlib
        import importlib.util
        import io
        import json
        import os
        import subprocess
        import tempfile
        import venv
        from types import SimpleNamespace
        from unittest.mock import Mock, patch

        if os.name == "nt":
            self.skipTest("Unix executable symlink regression")
        spec = importlib.util.spec_from_file_location(
            "integrated_checks", ROOT / "evidence/instantiation/20260908-p2-integrated/checks.py"
        )
        recorder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recorder)
        real_run = subprocess.run
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            env_dir = work / "venv"
            venv.EnvBuilder(with_pip=False, symlinks=True).create(env_dir)
            python = env_dir / "bin/python"
            self.assertTrue(python.is_symlink())
            cli = python.parent / "uppaal-verifyta"
            probe = "import sys; print(sys.prefix)"
            cli.write_text(f"#!{python}\n{probe}\n", encoding="utf-8")
            cli.chmod(0o755)
            observed = []

            def run_probe(command, **kwargs):
                observed.append(command)
                if command[0] == "git":
                    return subprocess.CompletedProcess(command, 0, b"", b"")
                if command[-1] == "list-examples":
                    self.assertEqual(command[0], str(cli))
                    result = real_run(command, **kwargs)
                else:
                    self.assertEqual(command[0], str(python))
                    result = real_run([command[0], "-c", probe], **kwargs)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.decode().strip(), str(env_dir))
                return result

            output = work / "run"
            argv = ["checks.py", "--output", str(output), "--python",
                    os.path.relpath(python, Path.cwd())]
            with patch.object(recorder.sys, "argv", argv), \
                 patch.object(recorder, "subprocess", SimpleNamespace(
                     check_output=Mock(side_effect=["", "test-commit\n"]),
                     run=run_probe, TimeoutExpired=subprocess.TimeoutExpired)), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(recorder.main(), 0)
            report = json.loads((output / "checks.json").read_text())
            self.assertEqual(report["python"], str(python))
            self.assertEqual(len(observed), 9)
            self.assertTrue(all(item["exit_code"] == 0 for item in report["commands"]))


if __name__ == "__main__":
    unittest.main()
