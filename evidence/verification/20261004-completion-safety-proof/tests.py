"""Premise-breaking mutations operate below the outer input-hash check."""
import copy
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import check

class PremiseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.parse(check.ROOT/check.MODEL).getroot()
        cls.query = (check.ROOT/check.QUERY).read_text()
        cls.expected = json.loads((check.HERE/"premises.json").read_text())

    def checked(self, root=None, query=None):
        return check.check_premises(root if root is not None else self.root,
                                    query if query is not None else self.query, self.expected)

    def edge(self, root, name, index):
        return next(t for t in root.findall("template") if t.findtext("name")==name).findall("transition")[index]

    def template(self, root, name):
        return next(t for t in root.findall("template") if t.findtext("name")==name)

    def reject_edge(self, name, index, kind, old, new, reason):
        root = copy.deepcopy(self.root)
        e = self.edge(root,name,index)
        label = e.find("label[@kind='"+kind+"']")
        self.assertIn(old,label.text)
        label.text = label.text.replace(old,new,1)
        with self.assertRaisesRegex(check.PremiseError,reason):
            self.checked(root)

    def test_exact_full_model_and_reproducible_certificate(self):
        actual = check.run()
        self.assertEqual(actual,json.loads((check.HERE/"certificate.json").read_text()))

    def test_byte_gate_rejects_changed_model(self):
        self.assertNotEqual(check.sha(ET.tostring(self.root)),check.MODEL_HASH)

    def test_missing_receipt(self):
        self.reject_edge(check.APP,12,"assignment","c82_received=true","c82_received=false","entry does not")

    def test_wrong_received_id(self):
        self.reject_edge(check.APP,12,"assignment","c82_received_request_id=c82_tx_request_id","c82_received_request_id=0","entry does not")

    def test_lost_quality_guard(self):
        self.reject_edge(check.APP,12,"guard","c82_payload_quality()","true","entry does not")

    def test_freshness_equality_is_not_strict(self):
        self.reject_edge(check.APP,12,"guard","c82_sample_age<5","c82_sample_age<=5","strict receipt freshness")

    def test_deadline_removed(self):
        self.reject_edge(check.APP,12,"guard","c82_service_age<=c82_D_service","true","receipt deadline")

    def test_wrong_retrospective_band(self):
        self.reject_edge(check.APP,13,"assignment","c82_receipt_service_band=2","c82_receipt_service_band=1","receipt band mismatch")

    def test_request_stays_active(self):
        self.reject_edge(check.APP,12,"assignment","c82_active=false","c82_active=true","retire the request")

    def test_timer_replaces_delivery(self):
        self.reject_edge(check.APP,12,"synchronisation","c82_result_delivery?","u0_app_service_complete?","actual delivery")

    def test_sender_overwrites_guarded_data(self):
        root=copy.deepcopy(self.root)
        ET.SubElement(self.edge(root,check.JOB,7),"label",kind="assignment").text="c82_tx_request_id=0"
        with self.assertRaisesRegex(check.PremiseError,"sender can invalidate"):
            self.checked(root)

    def test_completed_has_exit(self):
        root=copy.deepcopy(self.root)
        e=copy.deepcopy(self.edge(root,check.APP,2))
        e.find("source").set("ref","u0_app_id7")
        self.template(root,check.APP).append(e)
        with self.assertRaisesRegex(check.PremiseError,"absorbing"):
            self.checked(root)

    def test_completed_initial(self):
        root=copy.deepcopy(self.root)
        self.template(root,check.APP).find("init").set("ref","u0_app_id7")
        with self.assertRaisesRegex(check.PremiseError,"initial state"):
            self.checked(root)

    def test_new_unconditional_writer(self):
        root=copy.deepcopy(self.root)
        e=self.edge(root,"u0_phy_Template_A_CH",0)
        lab=e.find("label[@kind='assignment']")
        lab.text += ", c82_success=false"
        with self.assertRaisesRegex(check.PremiseError,"unclassified record writer"):
            self.checked(root)

    def test_late_cancel_changes_success(self):
        self.reject_edge(check.ENV,6,"assignment","c82_cancelled=(c82_active || c82_cancelled)","c82_cancelled=true","identity rule")

    def test_late_cancel_changes_outcome(self):
        self.reject_edge(check.ENV,12,"assignment","c82_outcome=(c82_active ? 5 : c82_outcome)","c82_outcome=5","identity rule")

    def test_loss_allowed_after_success(self):
        self.reject_edge(check.JOB,8,"guard","c82_active && ","","unclassified record writer")

    def test_shared_helper_loses_active_gate(self):
        root=copy.deepcopy(self.root)
        d=root.find("declaration")
        d.text=d.text.replace("server==0 && c82_active && c82_enqueued","server==0 && c82_enqueued")
        with self.assertRaisesRegex(check.PremiseError,"lacks active check"):
            self.checked(root)

    def test_extra_clock_reset(self):
        self.reject_edge(check.JOB,6,"assignment","c82_tx_age=0","c82_tx_age=0, c82_sample_age=0","reviewed premise differs")

    def test_measurement_can_be_reused(self):
        root=copy.deepcopy(self.root)
        d=root.find("declaration")
        d.text=d.text.replace("c82_sampled=true; c82_sample_age=0","c82_sampled=false; c82_sample_age=0")
        with self.assertRaisesRegex(check.PremiseError,"c82_helpers"):
            self.checked(root)

    def test_fake_initialized_sample(self):
        root=copy.deepcopy(self.root)
        d=root.find("declaration")
        d.text=d.text.replace("c82_sampled=false;","c82_sampled=true;",1)
        with self.assertRaisesRegex(check.PremiseError,"declaration_remainder"):
            self.checked(root)

    def test_duplicate_instance(self):
        root=copy.deepcopy(self.root)
        root.find("system").text += "\nrogue = u0_app_A_REQ();"
        with self.assertRaisesRegex(check.PremiseError,"system"):
            self.checked(root)

    def test_local_shadow(self):
        root=copy.deepcopy(self.root)
        t=self.template(root,check.APP)
        d=t.find("declaration")
        if d is None: d=ET.SubElement(t,"declaration")
        d.text="bool c82_active=true;"
        with self.assertRaisesRegex(check.PremiseError,"local_scopes"):
            self.checked(root)

    def test_indirect_writer_in_existing_helper(self):
        root=copy.deepcopy(self.root)
        d=root.find("declaration")
        d.text=d.text.replace("void u0_app_note_kpi_update_event() {","void u0_app_note_kpi_update_event() { c82_cancelled=true;")
        with self.assertRaisesRegex(check.PremiseError,"reviewed premise differs"):
            self.checked(root)

    def test_weakened_query_rejected(self):
        with self.assertRaisesRegex(check.PremiseError,"query differs"):
            self.checked(query=self.query.replace("c82_success && ",""))

    def test_layout_comment_variation_is_semantically_accepted(self):
        root=copy.deepcopy(self.root)
        self.template(root,check.APP).find("location").set("x","12345")
        root.find("declaration").text += "\n// harmless presentation comment\n"
        self.assertTrue(self.checked(root)["premises_supported"])

    def test_equality_calculus_does_not_assert_unknown(self):
        f=check.Facts(["a==b","b==1","!bad"])
        self.assertTrue(f.proves("a==1"))
        self.assertTrue(f.proves("!bad"))
        self.assertFalse(f.proves("a==0"))
        self.assertFalse(f.proves("unknown()"))

if __name__=="__main__":
    unittest.main(verbosity=2)
