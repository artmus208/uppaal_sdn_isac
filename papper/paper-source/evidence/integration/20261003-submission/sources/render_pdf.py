from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(P/'build/tools'))
import fitz
from PIL import Image,ImageOps,ImageDraw
pdf=Path(sys.argv[1]) if len(sys.argv)>1 else P/'MoNoTeC-2026-paper.pdf'
out=P/'qa'/(sys.argv[2] if len(sys.argv)>2 else pdf.stem);out.mkdir(parents=True,exist_ok=True)
doc=fitz.open(pdf)
for i,p in enumerate(doc):
    p.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False).save(out/f'page-{i+1}.png')
for start in range(0,len(doc),4):
    thumbs=[]
    for i in range(start,min(start+4,len(doc))):
        im=Image.open(out/f'page-{i+1}.png');im.thumbnail((610,860))
        thumb=Image.new('RGB',(630,900),'#DDDDDD');thumb.paste(im,((630-im.width)//2,25))
        ImageDraw.Draw(thumb).text((12,8),f'Page {i+1}',fill='black');thumbs.append(thumb)
    sheet=Image.new('RGB',(1260,1800),'white')
    for j,im in enumerate(thumbs):sheet.paste(im,((j%2)*630,(j//2)*900))
    sheet.save(out/f'contact-{start+1}.png')
(out/'text.txt').write_text('\n\f\n'.join(p.get_text() for p in doc),encoding='utf-8')
for f in (P/'figures').glob('*.pdf'):
    fdoc=fitz.open(f)
    fdoc[0].get_pixmap(matrix=fitz.Matrix(800/72,800/72),alpha=False).save(f.with_suffix('.png'))
print(json.dumps({'file':str(pdf),'pages':len(doc),'qa':str(out)}))
