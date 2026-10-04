"""Read-only re-audit of preserved evidence; never launches an engine."""
import argparse
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import check

HERE, ROOT = check.HERE, check.ROOT
CAND = "evidence/instantiation/uav-service-completion-candidate"
CAMPAIGN = "evidence/verification/uav-service-completion-p3-20261002"

def run():
    pins = json.loads((HERE/"history-pins.json").read_text())
    for name, digest in pins.items():
        check.require(check.sha((ROOT/name).read_bytes()) == digest, "historical drift: "+name)
    cp, hp = ROOT/CAND, ROOT/CAMPAIGN
    replay = json.loads((cp/"runs/replay-001/result.json").read_text())
    prov = json.loads((cp/"runs/replay-001/provenance.json").read_text())
    check.require(replay["model_hash"] == check.MODEL_HASH, "replay model")
    check.require(replay["status"] == "replay_complete" and replay["goal"], "historical replay result")
    check.require(replay["property_verdict"] is None and replay["query_hash"] is None, "simulation is not a verdict")
    raw_index = json.loads((cp/"raw-index.json").read_text())
    with zipfile.ZipFile(cp/"raw-traces.zip") as z:
        names = ["runs/replay-001/steps.jsonl", "runs/replay-001/stdout.txt",
                 "runs/replay-001/reachable-prefix.xtr", "runs/simulate-006/trace.xtr"]
        archive_hashes = {}
        for name in names:
            data = z.read(name)
            check.require(check.sha(data) == raw_index[name]["sha256"], "raw archive hash")
            archive_hashes[name] = check.sha(data)
        check.require(archive_hashes["runs/simulate-006/trace.xtr"] == replay["input_hash"], "replay input trace")
        steps = [json.loads(x) for x in z.read(names[0]).splitlines()]
    check.require(len(steps) == 101 and replay["accepted_transitions"] == 100, "replay length")
    root = ET.parse(ROOT/check.MODEL).getroot()
    system = root.findtext("system")
    instances = system.split("system ",1)[1].split(";",1)[0].replace(" ","").replace("\n","").split(",")
    binding = dict(re.findall(r"(\w+)\s*=\s*(\w+)\(\);",system))
    table = {(e["template"],e["index"]):e for e in check.edges(root)}
    variable_names = replay["variable_names"]
    record = []
    first = {}
    flags = ["c82_request_id","c82_admitted","c82_sampled","c82_enqueued",
             "c82_dispatched","c82_attempted","c82_received","c82_success"]
    expected_anchor = {
        "c82_request_id":(check.APP,2), "c82_admitted":(check.APP,3),
        "c82_sampled":(check.PHY,25), "c82_enqueued":("SharedLoad",5),
        "c82_dispatched":("SharedLoad",1), "c82_attempted":(check.JOB,6),
        "c82_received":(check.APP,12), "c82_success":(check.APP,12)}
    for i, s in enumerate(steps):
        check.require(s["state_index"] == i,"replay state order")
        values = dict(zip(variable_names, s["snapshot"]["values"]))
        taken = []
        for clause in s.get("edges","").split(";"):
            fields = clause.split()
            if not fields:
                continue
            # Remaining integers are selected values, not another process/edge pair.
            check.require(len(fields)>=2 and all(x.lstrip("-").isdigit() for x in fields),
                          "malformed engine edge key")
            a,b = fields[:2]
            key = (binding[instances[int(a)]],int(b))
            check.require(key in table,"unknown recorded edge")
            taken.append(key)
        for flag in flags:
            if values[flag] and flag not in first:
                check.require(i>0 and expected_anchor[flag] in taken,"causal anchor "+flag)
                first[flag]=i
                record.append({"record":flag,"first_state":i,"engine_edges":s["edges"],
                               "xml_template":expected_anchor[flag][0],
                               "xml_edge":expected_anchor[flag][1]})
    order = [first[x] for x in flags[:-1]]
    check.require(all(a<b for a,b in zip(order,order[1:])),"causal order")
    final = dict(zip(variable_names,steps[-1]["snapshot"]["values"]))
    check.require(steps[-1]["snapshot"]["locations"][instances.index("u0_app_Req_0")] == "Completed","terminal APP")
    check.require(final["c82_active"]==0 and final["c82_outcome"]==1,"successful inactive record")
    check.require(all(final[k]==0 for k in ("c82_cancelled","c82_tx_lost","c82_queue_failed","c82_sensing_failed")),"no failed receipt")
    ledger = json.loads((hp/"query-ledger.json").read_text())
    item = next(x for x in ledger["queries"] if x["query_id"]=="completion-safety")
    raw = json.loads((hp/item["result_path"]).read_text())
    check.require(raw["model_hash"]==check.MODEL_HASH and
                  raw["query_hash"]==check.sha((ROOT/check.QUERY).read_bytes()),"native input identity")
    check.require(raw["status"]=="timeout" and raw["verdict"] is None
                  and item["status"]=="timeout" and item["verdict"] is None,"native status preserved")
    attempt = hp/Path(item["result_path"]).parent
    stdout = (attempt/raw["stdout_reference"]).read_text()
    check.require("Formula is satisfied" not in stdout and "Formula is NOT satisfied" not in stdout,
                  "unexpected completed native verdict")
    return {
        "audit_kind":"static re-audit of saved historical evidence",
        "new_native_executions":0, "input_file_hashes":pins,
        "raw_archive_entries":archive_hashes, "causal_first_records":record,
        "historical_simulation":{
            "run_id":prov["run_id"],"status":replay["status"],
            "model_hash":replay["model_hash"],"query_hash":None,"property_verdict":None,
            "tool_version":replay["tool_version"],"source_commit":prov["source_commit"],
            "accepted_transitions":100,"stored_states":101,"completed_state_index":100,
            "limitation":"This reads historical engine output; no fresh engine replay or universal verdict."},
        "historical_model_checking":{
            **{k:raw[k] for k in ("status","verdict","model_hash","query_hash","tool_version",
                                  "elapsed_seconds","peak_rss_bytes","cpu_seconds","command")},
            "campaign_run_id":item["run_id"],"attempt_run_id":raw["run_id"],
            "source_commit":item["execution_source_commit"],
            "result":CAMPAIGN+"/"+item["result_path"]},
        "mathematical_argument":{"claim":"exact completion-safety plus inactive and causal receipt history",
                                  "acceptance_status":"pending_independent_review",
                                  "artifact":"proof.md"}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path)
    p.add_argument("--check",action="store_true")
    a=p.parse_args()
    result=run()
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.check:
        check.require((HERE/"historical-evidence.json").read_text()==text,"history certificate differs")
    elif a.output:
        a.output.write_text(text,encoding="utf-8",newline="\n")
    print(json.dumps({"new_native_executions":0,"historical_native_status":"timeout",
                      "historical_replay_transitions":100,"causal_record_states":
                      [x["first_state"] for x in result["causal_first_records"]]}))
if __name__=="__main__":
    main()
