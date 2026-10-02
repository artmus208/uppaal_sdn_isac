"""Derive review tables from the independently audited full engine replay."""
import csv
import io
import json
import re
import xml.etree.ElementTree as ET

import audit

HERE=audit.HERE


def bound(raw):
    return {'bound':raw>>1,'strict':not bool(raw&1),'raw':raw}


def interval(zone,index):
    lower=bound(zone[0][index]);upper=bound(zone[index][0])
    lower['bound']=-lower['bound']
    return {'lower':lower,'upper':upper}


def dump(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def main():
    result=audit.audit();replay=audit.data('runs/replay-001/result.json')
    states=audit.events('replay-001');names=replay['variable_names'];clocks=replay['clock_names']
    instances=audit.data('instance-vector.json')['system_order']
    root=ET.fromstring((HERE/'model.xml').read_bytes())
    templates={t.findtext('name'):t for t in root.findall('template')}
    bindings=dict(re.findall(r'(\w+)\s*=\s*(\w+)\([^;]*\);',root.findtext('system')))
    out=io.StringIO();writer=csv.writer(out,lineterminator='\n')
    writer.writerow(['state_index','edges','named_transitions','post_state_time_zone','changed_variables'])
    for before,after in zip(states,states[1:]):
        transitions=[]
        for part in after['edges'].split(';'):
            fields=part.strip().split()
            if not fields:continue
            process,edge=map(int,fields[:2]);instance=instances[process]
            t=templates[bindings[instance]];e=t.findall('transition')[edge]
            locations={l.get('id'):l.findtext('name') for l in t.findall('location')}
            sync=next((l.text for l in e.findall('label') if l.get('kind')=='synchronisation'),'')
            transitions.append(f'{instance}:{edge} {locations[e.find("source").get("ref")]}->{locations[e.find("target").get("ref")]} {sync}')
        changes={n:[a,b] for n,a,b in zip(names,before['snapshot']['values'],after['snapshot']['values']) if a!=b}
        writer.writerow([after['state_index'],after['edges'],'; '.join(transitions),
            json.dumps(interval(after['snapshot']['zone'],clocks.index('u0_bus_time')),sort_keys=True),json.dumps(changes,sort_keys=True)])
    (HERE/'replay-steps.csv').write_text(out.getvalue())
    terminal=states[-1]['snapshot'];zone=terminal['zone']
    receipt={'run_id':result['runs'][6]['run_id'],'state_index':100,
       'model_hash':result['model_hash'],'trace_hash':replay['trace_hash'],
       'clock_encoding':'DBM raw=2*bound+(1 for <=, 0 for <); cell i,j bounds clock_i-clock_j',
       'clock_bounds':{n:interval(zone,clocks.index(n)) for n in ['u0_bus_time','c82_service_age','c82_sample_age','c82_measure_age','c82_tx_age']},
       'request_emission_time_difference':{'upper':bound(zone[clocks.index('u0_bus_time')][clocks.index('c82_service_age')]),
           'negative_lower':bound(zone[clocks.index('c82_service_age')][clocks.index('u0_bus_time')])},
       'measurement_time_difference':{'upper':bound(zone[clocks.index('u0_bus_time')][clocks.index('c82_sample_age')]),
           'negative_lower':bound(zone[clocks.index('c82_sample_age')][clocks.index('u0_bus_time')])},
       'immutable_receipt_values':{n:v for n,v in zip(names,terminal['values']) if n.startswith('c82_')},
       'app_location':terminal['locations'][16],
       'interpretation':'Clock differences are read from one consistent replay DBM; intermediate post-state zones may include delay closure.'}
    dump('completion-record.json',receipt)
    result['parameter_set']='parameters.json';result['instance_vector']='instance-vector.json'
    result['query_registry']='inventory.json';result['artifact_inventory']='artifacts-sha256.json'
    result['trace_steps']='replay-steps.csv';result['completion_record']='completion-record.json'
    dump('results.json',result)


if __name__=='__main__':main()
