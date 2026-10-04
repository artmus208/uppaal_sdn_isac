"""Reproduce XML-derived P7 diagrams. Does not import/run the model generator or verifier."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import re
import textwrap
import xml.etree.ElementTree as ET

import reportlab
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
MODEL = "evidence/instantiation/uav-service-completion-candidate/model.xml"
EXPECTED = "b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02"
BASE = "452571598d4a5c1e070dace3a918ea737904e239"
INPUT = "61386aa358805082b705dcd00c8cbfde5fb98248"
WIDTH = 122 / 25.4 * 72
INK, MUTED, BORDER, FILL = "#172b3a", "#455562", "#71818c", "#f2f5f7"
FONT_DIR = Path(reportlab.__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont("Vera", str(FONT_DIR / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("VeraBd", str(FONT_DIR / "VeraBd.ttf")))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def structural(e):
    # Discard only XML drawing positions and transition bend points.
    if e.tag == "nail":
        return None
    attrs = {k: v for k, v in e.attrib.items() if k not in {"x", "y"}}
    return [e.tag, attrs, (e.text or "").strip(), [v for c in e if (v := structural(c)) is not None]]


class Diagram:
    """One coordinate system for editable SVG and embedded-font vector PDF."""
    def __init__(self, name, height, templates):
        self.name, self.h, self.templates = name, height, templates
        self.c = canvas.Canvas(str(ROOT / "figures" / f"fig-{name}.pdf"),
                               pagesize=(WIDTH, height), invariant=1, pageCompression=1)
        self.c.setTitle(f"P7 {name.upper()}: XML-derived fragments, baseline N=1")
        self.c.setAuthor("P7 / artmus208")
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="122mm" height="{height/72*25.4:.4f}mm" viewBox="0 0 {WIDTH} {height}">',
                    '<rect width="100%" height="100%" fill="white"/>',
                    '<desc>XML-derived explanatory fragments. Transition identifiers expand to exact XML labels in exact-labels.json and exact-labels.tex. Not a UPPAAL native export.</desc>']
        self.used_edges, self.used_locations, self.geometry = {}, {}, []
        self.bounds = []

    def text(self, x, y, text, size=8.5, bold=False, center=False, color=INK):
        font = "VeraBd" if bold else "Vera"
        width = pdfmetrics.stringWidth(text, font, size)
        left = x-width/2 if center else x
        assert left >= -0.01 and left+width <= WIDTH+0.01, (self.name, text, left, width)
        assert 0 <= y <= self.h, (text, y)
        self.c.setFillColor(color)
        self.c.setFont(font, size)
        self.c.drawString(left, self.h-y, text)
        self.svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Bitstream Vera Sans,DejaVu Sans,Arial,sans-serif" font-size="{size}" font-weight="{"bold" if bold else "normal"}" text-anchor="{"middle" if center else "start"}">{html.escape(text)}</text>')
        self.bounds.append([left, y-size, left+width, y, text, size])

    def box(self, x, y, w, h, fill=FILL):
        self.c.setStrokeColor(BORDER)
        self.c.setFillColor(fill)
        self.c.setLineWidth(.65)
        self.c.roundRect(x-w/2, self.h-y-h/2, w, h, 4, fill=1, stroke=1)
        self.svg.append(f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{BORDER}" stroke-width=".65"/>')

    def path(self, points, arrow=True):
        self.c.setStrokeColor(INK)
        self.c.setFillColor(INK)
        self.c.setLineWidth(.8)
        p = self.c.beginPath()
        p.moveTo(points[0][0], self.h-points[0][1])
        for x, y in points[1:]:
            assert 0 <= x <= WIDTH and 0 <= y <= self.h
            p.lineTo(x, self.h-y)
        self.c.drawPath(p)
        self.svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="{INK}" stroke-width=".8"/>')
        if arrow:
            (x0,y0),(x,y) = points[-2:]
            a = math.atan2(y-y0,x-x0)
            ps = [(x,y)] + [(x-5*math.cos(a)+k*2.3*math.sin(a), y-5*math.sin(a)-k*2.3*math.cos(a)) for k in [-1,1]]
            p=self.c.beginPath();p.moveTo(ps[0][0],self.h-ps[0][1])
            for xx,yy in ps[1:]: p.lineTo(xx,self.h-yy)
            p.close();self.c.drawPath(p,fill=1,stroke=0)
            self.svg.append('<polygon points="'+' '.join(f'{xx},{yy}' for xx,yy in ps)+f'" fill="{INK}"/>')

    def node(self, prefix, state, x, y, w=100, h=38, initial=False):
        t=self.templates[prefix]
        loc=next(l for l in t.findall('location') if l.findtext('name')==state)
        self.used_locations.setdefault(prefix,set()).add(loc.get('id'))
        inv=[l.text for l in loc.findall('label') if l.get('kind')=='invariant']
        ordinal=t.findall('location').index(loc)+1
        key=f'I:{prefix}{ordinal:02}'
        self.box(x,y,w,h)
        # Break only the visible location name at camel-case boundaries.
        words=re.sub(r'(?<=[a-z])(?=[A-Z])',' ',state).split()
        lines=['']
        for word in words:
            candidate=lines[-1]+word
            if pdfmetrics.stringWidth(candidate,'Vera',8.5)>w-10 and lines[-1]: lines.append(word)
            else: lines[-1]=candidate
        if inv: lines.append(key)
        for i,line in enumerate(lines): self.text(x,y-(len(lines)-1)*5+3+i*10,line,8.5,center=True,color=MUTED if line==key else INK)
        if loc.find('committed') is not None: self.text(x+w/2-9,y-h/2+9,'C',7,bold=True)
        if loc.find('urgent') is not None: self.text(x+w/2-9,y-h/2+9,'U',7,bold=True)
        if initial:
            assert t.find('init').get('ref')==loc.get('id')
            self.path([(x-w/2-9,y),(x-w/2,y)])
        self.geometry.append({'kind':'location','template_prefix':prefix,'xml_id':loc.get('id'),'center':[x,y],'size':[w,h],'initial_marker':initial})

    def edge(self,prefix,ordinals,points,label_pos):
        t=self.templates[prefix]
        ts=[t.findall('transition')[i-1] for i in ordinals]
        pairs={(e.find('source').get('ref'),e.find('target').get('ref')) for e in ts}
        assert len(pairs)==1, 'Only exact parallel transitions may share an arrow'
        for a,b in pairs:
            assert a in self.used_locations[prefix] and b in self.used_locations[prefix]
        self.used_edges.setdefault(prefix,set()).update(ordinals)
        self.path(points)
        label='/'.join(f'{prefix}{i:02}' for i in ordinals)
        self.text(*label_pos,label,size=8.5,center=True)
        self.geometry.append({'kind':'transition_group','prefix':prefix,'ordinals_1_based':ordinals,'points':points,'label_pos':label_pos})

    def finish(self,caption):
        self.c.save()
        self.svg.append('</svg>')
        (ROOT/'sources'/f'fig-{self.name}.svg').write_text('\n'.join(self.svg)+'\n',encoding='utf-8')
        write_json(ROOT/'sources'/f'layout-{self.name}.json',self.geometry)
        parts=[]
        for prefix,t in self.templates.items():
            locs=t.findall('location'); edges=t.findall('transition'); names={l.get('id'):l.findtext('name') for l in locs}
            shown=self.used_edges.get(prefix,set()); shownloc=self.used_locations.get(prefix,set())
            parts.append({'prefix':prefix,'template':t.findtext('name'),
                'instance':INSTANCES[t.findtext('name')],
                'shown_locations':[{'id':l.get('id'),'name':names[l.get('id')]} for l in locs if l.get('id') in shownloc],
                'omitted_locations':[{'id':l.get('id'),'name':names[l.get('id')]} for l in locs if l.get('id') not in shownloc],
                'shown_transitions':[f'{prefix}{i:02}' for i in sorted(shown)],
                'omitted_transitions':[f'{prefix}{i:02}' for i in range(1,len(edges)+1) if i not in shown]})
        write_json(ROOT/'checks'/f'text-bounds-{self.name}.json',self.bounds)
        return {'figure_id':self.name,'representation':'XML-derived diagram of declared fragments',
            'source_commit':INPUT,'operational_base':BASE,'model_path':MODEL,'model_sha256':EXPECTED,
            'layout_xml_path':'sources/model.xml','layout_xml_sha256':sha(ROOT/'sources/model.xml'),
            'layout_geometry':f'sources/layout-{self.name}.json','layout_geometry_sha256':sha(ROOT/'sources'/f'layout-{self.name}.json'),
            'parts':parts,'dimensions_mm':[122,round(self.h/72*25.4,3)],'minimum_lettering_pt':7,
            'body_lettering_pt':8.5,'export_method':'ReportLab PDF + editable SVG; optional Ghostscript EPS derivative; no native UPPAAL export',
            'export_tool_version':reportlab.Version,'caption':caption,'file':f'figures/fig-{self.name}.pdf',
            'outputs':{f'figures/fig-{self.name}.pdf':sha(ROOT/'figures'/f'fig-{self.name}.pdf'),f'sources/fig-{self.name}.svg':sha(ROOT/'sources'/f'fig-{self.name}.svg')}}


TREE=ET.parse(ROOT/'sources/model.xml').getroot()
TEMPLATES={t.findtext('name'):t for t in TREE.findall('template')}
INSTANCES={template:instance for instance,template in re.findall(r'(\w+)\s*=\s*(\w+)\(\);',TREE.findtext('system'))}


def app():
    d=Diagram('app',435,{'A':TEMPLATES['u0_app_A_REQ']})
    d.text(4,12,'(a) Request and admission',9,bold=True)
    for name,x,y,w,h in [('ServiceIdle',50,45,80,34),('RequestBuild',172,45,90,38),('RequestReady',296,45,88,34),('RequestPending',172,112,110,38),('Accepted',58,185,100,38),('Rejected',172,185,90,34),('AcceptedDegraded',286,185,108,38)]:
        d.node('A',name,x,y,w,h,initial=name=='ServiceIdle')
    d.edge('A',[1],[(90,45),(127,45)],(108,34))
    d.edge('A',[2],[(217,45),(252,45)],(234,34))
    d.edge('A',[3],[(296,62),(296,83),(172,83),(172,93)],(236,78))
    d.edge('A',[4],[(142,131),(58,148),(58,166)],(89,140))
    d.edge('A',[5],[(202,131),(286,148),(286,166)],(256,140))
    d.edge('A',[6,12],[(172,131),(172,168)],(199,151))
    d.text(4,229,'(b) Admitted-service outcomes: Accepted',9,bold=True)
    d.node('A','Accepted',65,295,100,38)
    for name,y in [('Completed',267),('ServiceFailed',309),('ServiceTimeout',351),('Cancelled',393)]: d.node('A',name,278,y,112,32)
    d.edge('A',[13,14],[(115,290),(145,290),(145,267),(222,267)],(180,256))
    d.edge('A',[15,16,17],[(115,295),(160,295),(160,309),(222,309)],(179,301))
    d.edge('A',[18],[(115,300),(131,300),(131,351),(222,351)],(180,341))
    d.edge('A',[26],[(115,304),(121,304),(121,393),(222,393)],(181,383))
    d.text(4,427,'Transition IDs and invariant keys expand in the label table.',8,color=MUTED)
    return d.finish('Application request and service-outcome fragments from u0_app_A_REQ. Panel (a) shows request construction and admission; panel (b) repeats Accepted to show completion, failure, timeout and cancellation. Rejected is an admission outcome. KPI/degradation updates, cancellation from RequestPending, and AcceptedDegraded outcome edges are omitted and enumerated in the manifest. Parallel transitions share an arrow, with every transition identifier retained. C denotes a committed location; I keys denote exact invariants. The companion label table gives every displayed transition\'s exact XML guard, synchronization and update. These fragments do not assert reachability or universal service completion.')


def phy():
    d=Diagram('phy',246,{'S':TEMPLATES['u0_phy_Template_A_SQ']})
    d.text(4,12,'UAV measurement fragment',9,bold=True)
    d.node('S','SensingQoSOk',78,90,128,36)
    d.node('S','JobMeasuring',269,90,126,38)
    d.edge('S',[25],[(142,90),(206,90)],(174,79))
    d.edge('S',[26],[(249,109),(249,141),(58,141),(58,108)],(166,132))
    d.edge('S',[27],[(289,109),(289,182),(98,182),(98,108)],(193,173))
    d.edge('S',[28],[(269,71),(269,36),(78,36),(78,72)],(173,29))
    d.text(4,209,'S25  c82_sense_start?       S26  c82_measurement!',8)
    d.text(4,225,'S27  c82_sense_failure!     S28  guard: !c82_active',8)
    d.text(4,241,'Other A_SQ states and transitions are outside this fragment.',8,color=MUTED)
    return d.finish('Measurement fragment of u0_phy_Template_A_SQ for the admitted UAV job. It shows the sensing-start rendezvous, timed measurement outcome, sensing-failure alternative, and exit when the job is inactive. Only SensingQoSOk and JobMeasuring and their four job-related transitions are shown; initial and QoS-classification locations are omitted. The I key and transition identifiers expand to exact XML fields in the companion table. The drawing represents the frozen abstract acquisition logic, not a calibrated physical sensing model.')


def mac():
    d=Diagram('mac',365,{'M':TEMPLATES['u0_mac_Template_A_SCH']})
    d.text(4,12,'Scheduling decisions and PHY acknowledgement',9,bold=True)
    for name,x,y,w,h in [('Idle',55,45,86,32),('CollectKPI',172,45,92,38),('SelectMode',290,45,96,38),('ScheduleFailure',55,165,106,36),('ApplySchedule',290,165,106,36),('WaitPHYAck',172,250,108,38)]:
        d.node('M',name,x,y,w,h,initial=name=='Idle')
    d.node('M','Idle',290,329,96,32)  # same XML location, repeated to avoid a page-spanning return arc
    d.edge('M',[1],[(98,45),(126,45)],(112,34))
    d.edge('M',[2],[(218,45),(242,45)],(230,34))
    d.edge('M',[3],[(172,64),(172,102),(262,102),(262,147)],(216,95))
    d.edge('M',[4],[(278,64),(278,126),(72,126),(72,147)],(179,120))
    d.edge('M',[5],[(306,64),(306,147)],(325,111))
    d.edge('M',[6],[(290,183),(290,250),(226,250)],(310,220))
    d.edge('M',[7,10],[(172,269),(172,329),(242,329)],(208,321))
    d.edge('M',[8,11],[(118,250),(55,250),(55,183)],(86,241))
    d.edge('M',[9],[(35,147),(35,61)],(55,91))
    d.text(4,360,'Idle is repeated. Policy-reception self-loops are omitted.',8,color=MUTED)
    return d.finish('Scheduler fragment from u0_mac_Template_A_SCH. The graph covers KPI collection, constrained fallback, policy selection, command dispatch, PHY acknowledgement and scheduling failure. Idle is drawn twice but denotes the same XML location. Parallel acknowledgement/timeout transitions retain separate identifiers. Six policy-reception self-loops are omitted and listed in the manifest. I keys and transition IDs resolve to exact XML fields in the companion table. Result queueing and transport belong to other templates and are not attributed to this scheduler.')


def sdn():
    d=Diagram('sdn',436,{'P':TEMPLATES['u0_sdn_Template_A_POLICY'],'R':TEMPLATES['u0_sdn_Template_A_REC']})
    d.text(4,12,'(a) Policy selection',9,bold=True)
    d.node('P','PolicyIdle',59,44,100,34,initial=True)
    d.node('P','Evaluate',59,110,100,38)
    outcomes=[('NormalMode',36),('CommPriorityMode',85),('SensingBoostMode',134),('ConstrainedMode',183),('RejectByPolicy',232)]
    for name,y in outcomes: d.node('P',name,275,y,126,34)
    d.edge('P',[1,2,3],[(59,61),(59,91)],(102,80))
    for i,(_,y) in enumerate(outcomes):
        lane=193-i*15
        d.edge('P',[8-i],[(109,110),(lane,110),(lane,y),(212,y)],(176,y-8))
    d.text(4,275,'(b) Recovery dispatch fragment',9,bold=True)
    d.node('R','FailureDetected',64,345,116,38)
    for name,y in [('StandbySwitch',301),('ReactiveReembedding',354),('Rollback',408)]: d.node('R',name,275,y,132,40)
    d.edge('R',[3],[(122,340),(143,340),(143,301),(209,301)],(175,291))
    d.edge('R',[4],[(122,345),(185,345),(185,354),(209,354)],(171,338))
    d.edge('R',[5],[(122,350),(134,350),(134,408),(209,408)],(173,398))
    return d.finish('SDN/RIC policy-selection and recovery-dispatch fragments from two separate templates, u0_sdn_Template_A_POLICY and u0_sdn_Template_A_REC. Panel (a) shows evaluation and five policy outcomes; return-to-idle edges are omitted. Panel (b) shows dispatch from FailureDetected to standby switching, reactive re-embedding or rollback; fault entry, acknowledgements, recovery completion, timeout and failure-reporting edges are omitted. No edge connects the two panels. I keys and transition IDs expand to exact XML fields in the companion table. The diagram does not establish successful or bounded recovery.')


def labels(figures):
    out={}
    for f in figures:
        for part in f['parts']:
            prefix=part['prefix'];t=TEMPLATES[part['template']]
            locs=t.findall('location'); names={l.get('id'):l.findtext('name') for l in locs}
            shown={v['id'] for v in part['shown_locations']}
            for i,l in enumerate(locs,1):
                if l.get('id') in shown:
                    out[f'I:{prefix}{i:02}']={'kind':'location','template':part['template'],'xml_id':l.get('id'),'name':l.findtext('name'),
                        'initial':t.find('init').get('ref')==l.get('id'),'committed':l.find('committed') is not None,'urgent':l.find('urgent') is not None,
                        'invariants':[x.text for x in l.findall('label') if x.get('kind')=='invariant']}
            for i,tr in enumerate(t.findall('transition'),1):
                key=f'{prefix}{i:02}'
                if key in part['shown_transitions']:
                    out[key]={'kind':'transition','template':part['template'],'ordinal_1_based':i,
                        'source_id':tr.find('source').get('ref'),'source':names[tr.find('source').get('ref')],
                        'target_id':tr.find('target').get('ref'),'target':names[tr.find('target').get('ref')],
                        'labels':[dict(x.attrib,text=x.text or '') for x in tr.findall('label')]}
    return out


def latex_escape(s):
    return re.sub(r'([_&#%])',r'\\\1',s)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--only',choices=['app','phy','mac','sdn']);a=ap.parse_args()
    assert sha(ROOT/'sources/model.xml')==EXPECTED
    assert sha(REPO/MODEL)==EXPECTED
    source=ET.parse(REPO/MODEL).getroot()
    sem_equal=structural(source)==structural(TREE)
    assert sem_equal
    checks={'exact_source_bytes_equal':(REPO/MODEL).read_bytes()==(ROOT/'sources/model.xml').read_bytes(),
        'structural_semantics_equal':sem_equal,'source_sha256':EXPECTED,'layout_xml_sha256':sha(ROOT/'sources/model.xml'),
        'xml_modifications':[], 'layout_location':'Separate SVG/PDF geometry only; XML remains byte-identical'}
    write_json(ROOT/'checks/semantic-comparison.json',checks)
    functions={'app':app,'phy':phy,'mac':mac,'sdn':sdn}
    selected=[a.only] if a.only else ['app','phy','mac','sdn']
    figures=[functions[n]() for n in selected]
    exact=labels(figures);write_json(ROOT/'sources/exact-labels.json',exact)
    captions=[]
    tex=[r'\documentclass[runningheads]{llncs}',r'\usepackage[T1]{fontenc}',r'\usepackage{graphicx}',r'\usepackage{url}',r'\begin{document}',r'\pagestyle{plain}',r'\typeout{P7-TEXTWIDTH=\the\textwidth}']
    for f in figures:
        name=f['figure_id'];caption=latex_escape(f['caption'])
        captions.append(r'\newcommand{\PSeven'+name.capitalize()+r'Caption}{'+caption+'}')
        tex += [r'\begin{figure}[p]',r'\centering',r'\includegraphics[width=\textwidth]{'+f['file']+'}',r'\caption{'+caption+'}',r'\label{fig:p7-'+name+'}',r'\end{figure}',r'\clearpage']
    appendix=[r'\section*{Exact XML labels (companion tables)}',
        r'Transition identifiers use a template prefix and a one-based transition ordinal in the frozen XML. Parallel transitions are listed separately. Line wrapping below is typographical only. No guard, synchronization or update is replaced by an explanatory condition. Empty guard, synchronization or update fields are explicitly marked absent. Location invariant keys use the corresponding location ordinal. These tables must accompany any use of the abbreviated diagrams.']
    for key,v in exact.items():
        if v['kind']=='location':
            if not v['invariants']: continue
            lines=[key+' '+v['name']]+['Invariant: '+x for x in v['invariants']]
        else:
            lines=[key+' '+v['source']+' -> '+v['target']]
            for kind,word in [('guard','Guard'),('synchronisation','Synchronization'),('assignment','Update')]:
                values=[l['text'] for l in v['labels'] if l['kind']==kind]
                lines += [word+': '+(' ; '.join(values) if values else '(absent)')]
        wrapped='\n'.join('\n'.join(textwrap.wrap(line,width=68,break_long_words=True,break_on_hyphens=False,replace_whitespace=False)) for line in lines)
        appendix += [r'\begin{samepage}',r'\small',r'\begin{verbatim}',wrapped,r'\end{verbatim}',r'\normalsize',r'\end{samepage}']
    (ROOT/'exact-labels.tex').write_text('\n'.join(appendix)+'\n',encoding='utf-8')
    tex += [r'\input{exact-labels.tex}',r'\end{document}']
    (ROOT/'preview.tex').write_text('\n'.join(tex)+'\n',encoding='utf-8')
    (ROOT/'captions.tex').write_text('\n'.join(captions)+'\n',encoding='utf-8')
    manifest={'schema_version':1,'issue':91,'owner':'artmus208','reviewer_integrator':'vadimnbkg','baseline_id':'uav-service-completion-r1-20261002',
        'source_commit':INPUT,'operational_base':BASE,'model_sha256':EXPECTED,
        'baseline_manifest_sha256':'4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d',
        'generator_path':'evidence/instantiation/uav-service-completion-candidate/generate.py','generator_sha256':'a5310747b9e2f1b837d0fefdff26d04c9218b7f22a87672bfaa13e7ee58e0ba2',
        'generation_source_hash':'df56acfacd2b6655735ffd8bbcf52fe9ef648982b5a444d7e439520b86fdb79e',
        'label_mapping':'sources/exact-labels.json','label_mapping_sha256':sha(ROOT/'sources/exact-labels.json'),
        'xml_is_unmodified':True,'native_uppaal_export':False,'figures':figures,'independent_acceptance':'pending'}
    write_json(ROOT/'figure-manifest.json',manifest)
    print(json.dumps({'figures':selected,'semantic_comparison':checks,'textwidth_mm':122,'reportlab':reportlab.Version}))


if __name__=='__main__': main()
