"""Deterministic, hash-checked compiler for the full Issue #82 candidate."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'evidence/scalability/family-series-68/generated/n1/model.xml'
SOURCE_HASH = '5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385'
BASE = '91113a1b634f030c7e895f54f5c36a0b140d66eb'
PREFIX = 'c82_'

DECL = '''
// Issue #82: single admitted request, one measurement, one FIFO result token.
const int c82_D_service=40;
clock c82_service_age, c82_sample_age, c82_measure_age, c82_tx_age;
int[0,1] c82_request_id=0, c82_admitted_id=0, c82_job_id=0;
int[0,1] c82_sample_id=0, c82_sample_request_id=0;
int[0,1] c82_tx_request_id=0, c82_tx_sample_id=0;
int[0,1] c82_received_request_id=0, c82_received_sample_id=0;
bool c82_active=false, c82_admitted=false, c82_sampled=false;
bool c82_enqueued=false, c82_dispatched=false, c82_attempted=false;
bool c82_received=false, c82_success=false, c82_cancelled=false;
bool c82_sensing_failed=false, c82_tx_lost=false, c82_queue_failed=false;
bool c82_receipt_timely=false, c82_receipt_quality=false;
// Receipt bands are immutable retrospective records, not terminal clock guards.
int[0,2] c82_receipt_service_band=0, c82_receipt_sample_band=2;
// 0=open; 1=success; 2=admission rejection; 3=service failure;
// 4=service deadline; 5=cancellation. No request reuse in this abstraction.
int[0,5] c82_outcome=0;
int[0,u0_mac_queue_K] c82_fifo_rank=0;
int[0,2] c82_pd=2, c82_fa=2, c82_miss=2, c82_acc=2, c82_cov=2;
int[0,2] c82_req_pd=2, c82_req_fa=2, c82_req_miss=2;
int[0,2] c82_req_acc=2, c82_req_cov=2, c82_req_fresh=2, c82_req_update=2;
chan c82_sense_start, c82_measurement, c82_sense_failure;
chan c82_enqueue, c82_enqueue_loss, c82_result_delivery;

void c82_emit_request() {
  c82_request_id=1; c82_service_age=0; c82_active=true;
  c82_req_pd=u0_app_pdMinClass; c82_req_fa=u0_app_pfaMaxClass;
  c82_req_miss=u0_app_pmissMaxClass; c82_req_acc=u0_app_accuracyBoundClass;
  c82_req_cov=u0_app_coverageBoundClass;
  c82_req_fresh=u0_app_sensingFreshnessBoundClass;
  c82_req_update=u0_app_sensingUpdateBoundClass;
}
void c82_store_measurement() {
  c82_sample_id=1; c82_sample_request_id=c82_job_id;
  c82_sampled=true; c82_sample_age=0;
  c82_pd=u0_phy_PdClass; c82_fa=u0_phy_RfaClass;
  c82_miss=u0_bus_missed_detection; c82_acc=u0_phy_AccClass;
  c82_cov=u0_phy_CoverageClass;
}
bool c82_class_ok(int req, int value) {
  return (req==2 && value==0) || (req==1 && value!=2) || req==0;
}
bool c82_payload_quality() {
  return !(c82_pd==0 && c82_miss==2) && !(c82_pd==2 && c82_miss==0)
    && c82_class_ok(c82_req_pd,c82_pd) && c82_class_ok(c82_req_fa,c82_fa)
    && c82_class_ok(c82_req_miss,c82_miss) && c82_class_ok(c82_req_acc,c82_acc)
    && c82_class_ok(c82_req_cov,c82_cov)
    && c82_pd!=2 && c82_fa!=2 && c82_miss!=2 && c82_acc!=2 && c82_cov!=2;
}
void c82_queue_class() {
  u0_mac_queueClass=(u0_mac_queue_q==0 ? u0_mac_Q_EMPTY :
    (u0_mac_queue_q<=u0_mac_queue_L ? u0_mac_Q_LOW :
    (u0_mac_queue_q<=u0_mac_queue_M ? u0_mac_Q_MED :
    (u0_mac_queue_q<u0_mac_queue_H ? u0_mac_Q_HIGH : u0_mac_Q_CRIT))));
}
void c82_insert_result() {
  u0_mac_queue_q++; c82_fifo_rank=u0_mac_queue_q; c82_enqueued=true;
  c82_queue_class();
}
void c82_queue_overflow() {
  u0_mac_queue_q=u0_mac_queue_K+1; u0_mac_queue_overflow_seen=true;
  c82_queue_failed=true; c82_queue_class();
}
void c82_mac_service(int server) {
  // Called before the old aggregate dequeue/arrival update. Overflow stays absorbing.
  if (server==0 && c82_active && c82_enqueued && !c82_dispatched
      && u0_mac_queue_q<=u0_mac_queue_K && c82_fifo_rank>0) {
    if (c82_fifo_rank==1) {
      c82_fifo_rank=0; c82_dispatched=true;
      c82_tx_request_id=c82_sample_request_id; c82_tx_sample_id=c82_sample_id;
    } else c82_fifo_rank--;
  }
}
'''

# Clock predicates stay on edges: UPPAAL functions cannot snapshot real clocks to ints.
IDENTITY = ('c82_active && c82_admitted && c82_request_id==1 && '
            'c82_admitted_id==c82_request_id && c82_job_id==c82_request_id && '
            'c82_sampled && c82_sample_id==1 && c82_sample_request_id==c82_request_id && '
            'c82_enqueued && c82_dispatched && c82_attempted && '
            'c82_tx_request_id==c82_request_id && c82_tx_sample_id==c82_sample_id && '
            '!c82_received && !c82_cancelled && !c82_sensing_failed && '
            '!c82_tx_lost && !c82_queue_failed && c82_outcome==0')
QUALITY = 'c82_payload_quality()'
# Historical band mapping: fresh/UPD_OK [0,5), stale/slow [5,10), expired >=10.
# The only emitted request is strict. Keep clock constraints in a conjunction:
# UPPAAL constraint expressions cannot be nested into boolean preconditions.
IDENTITY += ' && c82_req_fresh==2 && c82_req_update==2'
FRESH = 'c82_sample_age<5'
RECEIPT = f'({IDENTITY}) && {QUALITY} && {FRESH} && c82_service_age<=c82_D_service'
RECORD = ('c82_received=true, c82_received_request_id=c82_tx_request_id, '
          'c82_received_sample_id=c82_tx_sample_id, c82_receipt_timely=true, '
          'c82_receipt_quality=true, c82_receipt_sample_band=0, c82_success=true, '
          'c82_active=false, c82_outcome=1, u0_bus_complete_delivered=true')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def label(edge, kind):
    return next((x for x in edge.findall('label') if x.get('kind')==kind), None)


def set_label(edge, kind, text):
    item=label(edge,kind)
    if item is None:
        item=ET.SubElement(edge,'label',kind=kind)
    item.text=text


def append_assignment(edge, text):
    old=label(edge,'assignment')
    set_label(edge,'assignment',(old.text+', ' if old is not None and old.text else '')+text)


def location(t, name, invariant=None, committed=False):
    ident=f'c82_{t.findtext("name")}_{name}'
    loc=ET.SubElement(t,'location',id=ident,x=str(100*len(t.findall('location'))),y='300')
    ET.SubElement(loc,'name').text=name
    if invariant: ET.SubElement(loc,'label',kind='invariant').text=invariant
    if committed: ET.SubElement(loc,'committed')
    return ident


def edge(t, source, target, guard=None, sync=None, assignment=None):
    e=ET.SubElement(t,'transition')
    ET.SubElement(e,'source',ref=source); ET.SubElement(e,'target',ref=target)
    for kind,text in [('guard',guard),('synchronisation',sync),('assignment',assignment)]:
        if text: set_label(e,kind,text)
    return e


def compile_model(data):
    if sha(data)!=SOURCE_HASH: raise ValueError('Frozen compiler input hash mismatch')
    root=ET.fromstring(data); original=copy.deepcopy(root)
    root.find('declaration').text+=DECL
    templates={t.findtext('name'):t for t in root.findall('template')}
    app=templates['u0_app_A_REQ']; old=list(app.findall('transition'))
    names={l.findtext('name'):l.get('id') for l in app.findall('location')}
    append_assignment(old[2],'c82_emit_request()')
    for n in [3,4]:
        set_label(old[n],'guard',f'({label(old[n],"guard").text}) && c82_active')
        append_assignment(old[n],'c82_admitted=true, c82_admitted_id=c82_request_id')
    for n in [5,13]:
        set_label(old[n],'guard',f'({label(old[n],"guard").text}) && c82_active')
        append_assignment(old[n],'c82_active=false, c82_outcome=2')
    for n in [11,12]: app.remove(old[n])
    for name in ['Accepted','AcceptedDegraded']:
        loc=next(l for l in app.findall('location') if l.get('id')==names[name])
        ET.SubElement(loc,'label',kind='invariant').text='c82_service_age<=c82_D_service'
    failed=location(app,'ServiceFailed'); timeout=location(app,'ServiceTimeout'); cancelled=location(app,'Cancelled')
    for source in ['Accepted','AcceptedDegraded']:
        for age_guard,band in [('c82_service_age<c82_D_service',1),('c82_service_age==c82_D_service',2)]:
            edge(app,names[source],names['Completed'],f'({RECEIPT}) && {age_guard}',
                 'c82_result_delivery?',RECORD+f', c82_receipt_service_band={band}')
        invalid_record='c82_received=true, c82_received_request_id=c82_tx_request_id, c82_received_sample_id=c82_tx_sample_id, c82_active=false, c82_outcome=3'
        edge(app,names[source],failed,f'c82_active && (!({IDENTITY}) || !{QUALITY})',
             'c82_result_delivery?',invalid_record)
        edge(app,names[source],failed,f'({IDENTITY}) && {QUALITY} && c82_sample_age>=5',
             'c82_result_delivery?',invalid_record)
        edge(app,names[source],failed,'c82_active && (c82_sensing_failed || c82_tx_lost || c82_queue_failed)',
             assignment='c82_active=false, c82_outcome=3')
        edge(app,names[source],timeout,'c82_active && c82_service_age==c82_D_service',
             assignment='c82_active=false, c82_outcome=4')
    for source in ['RequestPending','Accepted','AcceptedDegraded']:
        edge(app,names[source],cancelled,'c82_cancelled')

    env=templates['u0_Boundary_E_SERVICE']; old=list(env.findall('transition'))
    env.remove(old[2]); env.remove(old[3])
    for l in list(env.findall('location')):
        if l.findtext('name')=='CompleteCheck': env.remove(l)
        if l.findtext('name')=='Run':
            for a in list(l.findall('label')):
                if a.get('kind')=='invariant': l.remove(a)
    for n in [8,14,20]:
        append_assignment(old[n],'c82_cancelled=(c82_active || c82_cancelled), c82_outcome=(c82_active ? 5 : c82_outcome), c82_active=false')
    env_last=label(old[22],'synchronisation'); old[22].remove(env_last)

    sq=templates['u0_phy_Template_A_SQ']
    qos=next(l.get('id') for l in sq.findall('location') if l.findtext('name')=='SensingQoSOk')
    measuring=location(sq,'JobMeasuring','c82_measure_age<=u0_phy_D_sense')
    edge(sq,qos,measuring,'c82_active && c82_admitted && !c82_sampled',
         'c82_sense_start?','c82_measure_age=0')
    healthy=('c82_active && c82_job_id==c82_request_id && !c82_sampled && '
             'u0_phy_highest_priority_SQ()!=u0_phy_SENSINGSTATE_SENSINGFAILURE && '
             'u0_phy_PdClass!=u0_phy_PDCLASS_FAILED && '
             '!(u0_phy_PdClass==0 && u0_bus_missed_detection==2)')
    edge(sq,measuring,qos,'c82_measure_age==u0_phy_D_sense && '+healthy,
         'c82_measurement!','c82_store_measurement()')
    edge(sq,measuring,qos,'c82_measure_age==u0_phy_D_sense && c82_active',
         'c82_sense_failure!','c82_sensing_failed=true')
    edge(sq,measuring,qos,'!c82_active')

    shared=templates['SharedLoad']; old=shared.findall('transition')
    a=label(old[1],'assignment'); a.text='c82_mac_service(server), '+a.text
    wait=next(l.get('id') for l in shared.findall('location') if l.findtext('name')=='Wait')
    edge(shared,wait,wait,'c82_active && c82_sampled && !c82_enqueued && u0_mac_queue_q<u0_mac_queue_K',
         'c82_enqueue?','c82_insert_result()')
    edge(shared,wait,wait,'c82_active && c82_sampled && !c82_enqueued && u0_mac_queue_q>=u0_mac_queue_K',
         'c82_enqueue_loss!','c82_queue_overflow()')

    job=ET.Element('template'); ET.SubElement(job,'name').text='C82_ResultJob'
    locations={name:location(job,name, 'c82_tx_age<=u0_bus_D_bus' if name=='Transmitting' else None)
               for name in ['Idle','Ready','Measuring','ResultReady','Queued','Transmitting','Done']}
    ET.SubElement(job,'init',ref=locations['Idle'])
    edge(job,locations['Idle'],locations['Ready'],'c82_active && c82_admitted',assignment='c82_job_id=c82_admitted_id')
    edge(job,locations['Ready'],locations['Measuring'],'c82_active','c82_sense_start!')
    edge(job,locations['Measuring'],locations['ResultReady'],'c82_active','c82_measurement?')
    edge(job,locations['Measuring'],locations['Done'],sync='c82_sense_failure?')
    edge(job,locations['ResultReady'],locations['Queued'],'c82_active','c82_enqueue!')
    edge(job,locations['ResultReady'],locations['Done'],sync='c82_enqueue_loss?')
    edge(job,locations['Queued'],locations['Transmitting'],'c82_active && c82_dispatched',
         assignment='c82_attempted=true, c82_tx_age=0')
    edge(job,locations['Transmitting'],locations['Done'],'c82_active && c82_tx_age<=u0_bus_D_bus','c82_result_delivery!')
    edge(job,locations['Transmitting'],locations['Done'],'c82_active && c82_tx_age<=u0_bus_D_bus',
         assignment='c82_tx_lost=true')
    for name in ['Idle','Ready','Measuring','ResultReady','Queued','Transmitting']:
        edge(job,locations[name],locations['Done'],'c82_request_id==1 && !c82_active')
    index=list(root).index(root.find('system')); root.insert(index,job)
    system=root.find('system'); system.text=system.text.replace('system ', 'c82_job = C82_ResultJob();\nsystem ',1).rstrip().removesuffix(';')+', c82_job;\n'
    queries=root.find('queries')
    if queries is not None: root.remove(queries)
    # NTA readers require locations before init/transitions, including added locations.
    order={'name':0,'parameter':1,'declaration':2,'location':3,'init':4,'transition':5}
    for t in root.findall('template'):
        t[:]=sorted(t,key=lambda item:order[item.tag])
    ET.indent(root,space='  ')
    xml=b'<?xml version="1.0" encoding="utf-8"?>\n'+ET.tostring(root,encoding='utf-8')+b'\n'
    changed=[]
    for before,after in zip(original.findall('template'),root.findall('template')):
        if ET.tostring(before)!=ET.tostring(after):
            # Compare normalized elements to avoid serialization whitespace-only differences.
            ET.indent(before,space='  ');ET.indent(after,space='  ')
            if ET.tostring(before)!=ET.tostring(after): changed.append(after.findtext('name'))
    return xml, root, changed


def outputs():
    data=SOURCE.read_bytes();xml,root,changed=compile_model(data)
    queries={
        'success':'E<> u0_app_Req_0.Completed && c82_success',
        'completion-safety':('A[] (u0_app_Req_0.Completed imply (c82_success && c82_received && '
          'c82_admitted && c82_request_id==c82_received_request_id && '
          'c82_sample_id==c82_received_sample_id && c82_job_id==c82_request_id && '
          'c82_admitted_id==c82_request_id && c82_tx_request_id==c82_request_id && '
          'c82_tx_sample_id==c82_sample_id && c82_payload_quality() && '
          'c82_req_fresh==2 && c82_req_update==2 && '
          'c82_sample_request_id==c82_request_id && c82_enqueued && c82_dispatched && '
          'c82_attempted && c82_sampled && c82_receipt_timely && c82_receipt_quality && '
          'c82_receipt_sample_band==0 && c82_receipt_service_band>0 && '
          '!c82_cancelled && !c82_sensing_failed && !c82_tx_lost && !c82_queue_failed && c82_outcome==1))'),
        'admitted':'E<> c82_admitted', 'measurement':'E<> c82_sampled',
        'enqueue':'E<> c82_enqueued', 'attempt':'E<> c82_attempted',
        'loss':'E<> c82_tx_lost && u0_app_Req_0.ServiceFailed',
        'timeout':'E<> u0_app_Req_0.ServiceTimeout',
        'cancel':'E<> u0_app_Req_0.Cancelled',
        'deadline-equality':'E<> c82_success && c82_receipt_service_band==2',
        'deadlock':'A[] not deadlock',
    }
    generated={'model.xml':xml}
    for name,q in queries.items():generated[f'queries/{name}.q']=(q+'\n').encode()
    vector=json.loads((SOURCE.parent/'instance-vector.json').read_text())
    vector['configuration_id']='uav-service-completion-candidate-82-n1'
    vector['process_counts']['result_job']=1;vector['process_counts']['total']=51
    vector['system_order'].append('c82_job');vector['entities']['explicit_result_tokens']=1
    parameters={'candidate_id':vector['configuration_id'],'D_service':40,
      'D_service_provenance':'user confirmation in Issue #82, 2026-10-02 02:51:55 UTC',
      'measurement_duration':5,'measurement_provenance':'u0_phy_D_sense (new deliberate fixed-duration acquisition assumption)',
      'transmission_bound':1,'transmission_provenance':'u0_bus_D_bus (new lossy result transport assumption)',
      'freshness_mapping':{'fresh':'0<=sample_age<5','stale':'5<=sample_age<10','expired':'sample_age>=10'},
      'update_mapping':'UPD_OK/UPD_SLOW/UPD_VIOLATED uses the same sample-age bands as the historical B_KPI mapping; this is NOT a measured physical update period',
      'boundary_equalities':{'deadline40':'receipt may succeed; timeout is also enabled','sample_age5':'stale, strict request cannot succeed','sample_age10':'expired'},
      'single_request_bound':1,'single_sample_bound':1,'queue_capacity':4,
      'time_units':'abstract model units; no physical calibration','frozen_parameters_path':str(SOURCE.parent.relative_to(ROOT)/'parameters.json')}
    inventory={'candidate_id':vector['configuration_id'],'base_commit':BASE,'source_hash':SOURCE_HASH,
      'model_hash':sha(xml),'generator_hash':sha(Path(__file__).read_bytes()),
      'original_processes':50,'candidate_processes':51,'changed_templates':changed,
      'added_templates':['C82_ResultJob'],'added_instances':['c82_job'],
      'added_clocks':['c82_service_age','c82_sample_age','c82_measure_age','c82_tx_age'],
      'added_channels':['c82_sense_start','c82_measurement','c82_sense_failure','c82_enqueue','c82_enqueue_loss','c82_result_delivery'],
      'receipt_guard':RECEIPT,'queries':{n:{'formula':q,'hash':sha(generated[f'queries/{n}.q'])} for n,q in queries.items()},
      'templates':[{'name':t.findtext('name'),'locations':len(t.findall('location')),'transitions':len(t.findall('transition'))} for t in root.findall('template')]}
    for name,obj in [('instance-vector.json',vector),('parameters.json',parameters),('inventory.json',inventory)]:
        generated[name]=(json.dumps(obj,indent=2,sort_keys=True)+'\n').encode()
    # Every edited edge/location is enumerated, including the entire new job template.
    original=ET.fromstring(data);before={t.findtext('name'):t for t in original.findall('template')}
    changes={}
    for t in root.findall('template'):
        name=t.findtext('name')
        if name not in changed and name in before: continue
        changes[name]={'locations':[{'id':l.get('id'),'name':l.findtext('name'),'invariants':[x.text for x in l.findall('label') if x.get('kind')=='invariant'],'committed':l.find('committed') is not None,'urgent':l.find('urgent') is not None} for l in t.findall('location')],
           'transitions':[{'edge_index':i,'source':e.find('source').get('ref'),'target':e.find('target').get('ref'),'labels':{l.get('kind'):l.text for l in e.findall('label')}} for i,e in enumerate(t.findall('transition'))]}
    generated['changes.json']=(json.dumps(changes,indent=2,sort_keys=True)+'\n').encode()
    return generated


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for path,data in outputs().items():
        target=HERE/path
        if args.check:
            if not target.exists() or target.read_bytes()!=data: raise SystemExit(f'Drift: {path}')
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    print('Candidate reproduced' if args.check else 'Candidate generated')


if __name__=='__main__':main()
