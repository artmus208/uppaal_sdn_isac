"""Render selected, traceable XML transitions as publication-scale vector panels.

These are XML-derived diagrams, not UPPAAL screenshots. Full transition labels,
locations and omitted-edge indices are archived separately without rewriting XML.
"""
from pathlib import Path
import hashlib, json, xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

font_candidates=[(Path('C:/Windows/Fonts/arial.ttf'),Path('C:/Windows/Fonts/arialbd.ttf')),
                 (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))]
normal,bold=next(pair for pair in font_candidates if all(p.exists() for p in pair))
pdfmetrics.registerFont(TTFont('FigureSans',str(normal)))
pdfmetrics.registerFont(TTFont('FigureSans-Bold',str(bold)))

PACKAGE = Path(__file__).resolve().parent.parent
ROOT = PACKAGE.parents[2]
XML = ROOT / 'evidence/instantiation/uav-service-completion-candidate/model.xml'
EXPECTED = 'b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02'
raw = XML.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
root = ET.fromstring(raw)
specs = {
 'phy': ('u0_phy_Template_A_SQ', [(0,'channel report'),(3,'normal-scenario report'),(24,'admitted job starts'),(25,'measurement succeeds at 5'),(26,'measurement fails at 5'),(27,'inactive job retires')]),
 'mac': ('u0_mac_Template_A_SCH', [(0,'MAC tick'),(1,'PHY report received'),(2,'fallback on stale / deadline'),(3,'insufficient resources'),(4,'select finite policy'),(5,'send PHY command'),(6,'receive command ACK'),(7,'ACK deadline reached'),(8,'report schedule failure')]),
 'sdn': ('u0_sdn_Template_A_POLICY', [(0,'admission request'),(3,'reject predicate'),(4,'else: constrained predicate'),(5,'else: sensing-boost predicate'),(6,'else: comm-priority predicate'),(7,'else: normal mode')]),
 'app': ('u0_app_A_REQ', [(0,'new demand; build request'),(1,'request admissible / ready'),(2,'emit request; reset age'),(3,'accepted admission'),(5,'rejected admission'),(12,'valid receipt; age < 40'),(13,'valid receipt; age = 40'),(14,'invalid identity / quality'),(16,'sensing / loss / queue failure'),(17,'service age = 40'),(25,'cancellation')]),
}
out = PACKAGE / 'figures'; out.mkdir(exist_ok=True)
catalog = {'model_sha256':EXPECTED,'origin':'XML-derived transition fragments; not native UI exports','figures':{}}
for key,(name,rows) in specs.items():
    template = next(t for t in root.findall('template') if t.findtext('name')==name)
    locs = {n.attrib['id']:n.findtext('name',n.attrib['id']) for n in template.findall('location')}
    transitions=[]
    for i,t in enumerate(template.findall('transition')):
        transitions.append({'edge':i,'source':locs[t.find('source').attrib['ref']], 'target':locs[t.find('target').attrib['ref']], 'labels':[{**l.attrib,'text':l.text or ''} for l in t.findall('label')]})
    selected=[i for i,_ in rows]
    catalog['figures'][key]={'template':name,'selected_edges':selected,'omitted_edges':[i for i in range(len(transitions)) if i not in selected],'locations':[{**n.attrib,'name':locs[n.attrib['id']],'labels':[{**l.attrib,'text':l.text or ''} for l in n.findall('label')]} for n in template.findall('location')],'transitions':transitions}
    width=345.82677; height=26+len(rows)*31
    c=canvas.Canvas(str(out/f'{key}.pdf'), pagesize=(width,height), initialFontName='FigureSans')
    c.setTitle(f'{name}: selected XML transitions'); c.setAuthor('MoNoTeC manuscript integration')
    c.setFont('FigureSans',7.6); c.setFillColor(HexColor('#444444'))
    c.drawString(0,height-9,'SOURCE LOCATION')
    c.drawCentredString(width/2,height-9,'EDGE / EVENT SUMMARY')
    c.drawRightString(width,height-9,'TARGET LOCATION')
    for row,(idx,gloss) in enumerate(rows):
        t=transitions[idx]; y=height-31-row*31
        if row%2==0:
            c.setFillColor(HexColor('#F3F5F7')); c.rect(0,y-12,width,28,fill=1,stroke=0)
        c.setFillColor(black); c.setFont('FigureSans',8)
        c.drawString(3,y+3,t['source']); c.drawRightString(width-3,y+3,t['target'])
        c.setStrokeColor(HexColor('#435365')); c.setLineWidth(.6)
        c.line(112,y+4,width-112,y+4)
        p=c.beginPath();p.moveTo(width-112,y+4);p.lineTo(width-116,y+6);p.lineTo(width-116,y+2);p.close()
        c.setFillColor(HexColor('#435365')); c.drawPath(p,fill=1,stroke=0)
        c.setFillColor(black);c.setFont('FigureSans-Bold',7.5);c.drawCentredString(width/2,y+8,f'T{idx}')
        c.setFont('FigureSans',7.5);c.drawCentredString(width/2,y-8,gloss)
    c.showPage();c.save()
(out/'transition-catalogue.json').write_text(json.dumps(catalog,indent=2),encoding='utf-8')
lines=['# Figure provenance','','Four selected transition fragments derived directly from the unchanged S XML.',f'Model SHA256: `{EXPECTED}`.','', 'Edge indices are zero-based. Event summaries are explanatory glosses, not verbatim guards. Full guards, assignments, synchronization labels, location invariants and all omitted transitions are in transition-catalogue.json. The figure panels repeat a location when several selected transitions share it; they are not a new executable model.','']
for key,rec in catalog['figures'].items():
    lines += [f"## {key.upper()}: {rec['template']}", f"Included edges: {rec['selected_edges']}", f"Omitted edges: {rec['omitted_edges']}", '']
(out/'README.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'figures':list(specs),'model_sha256':EXPECTED}))
