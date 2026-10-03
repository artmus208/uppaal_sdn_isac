"""Create checked source ZIP and Windows delivery copies after the final commit."""
from pathlib import Path
import sys,subprocess,json,hashlib,zipfile,shutil
P=Path(__file__).resolve().parent.parent;R=P.parents[2]
DEST=Path(sys.argv[1]).resolve()
assert str(DEST).lower().startswith(str(Path.home()/'Desktop/Codex-MoNoTeC-20261003').lower()+'\\')
assert not DEST.exists(),'Choose a new output folder; existing user files are not overwritten'
def git(*args):return subprocess.check_output(['git','-C',str(R),*args])
head=git('rev-parse','HEAD').decode().strip();branch=git('branch','--show-current').decode().strip()
assert branch=='codex/vadimnbkg/92-monotec-submission'
assert not git('status','--porcelain').strip(),'Commit final changes before packaging'
selection=json.loads((P/'sources/evidence-bundle-paths.json').read_text(encoding='utf-8'))
paths=set(selection['paths'])
paths.update(['levels_tex/samplepaper.tex','monotec2026.bib'])
paths.update(x.decode() for x in git('ls-files','-z','evidence/integration/20261003-submission').split(b'\0') if x)
zip_path=P/'MoNoTeC-2026-source.zip'
members={}
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name in sorted(paths):
        path=(R/name).resolve();assert path.is_relative_to(R.resolve()) and path.is_file()
        data=path.read_bytes();z.writestr(name,data);members[name]=hashlib.sha256(data).hexdigest()
    for pin in selection['pinned_git_inputs']:
        for name in pin['paths']:
            assert name not in members
            data=git('show',pin['commit']+':'+name)
            z.writestr(name,data);members[name]=hashlib.sha256(data).hexdigest()
    z.writestr('SOURCE-MANIFEST.json',json.dumps({'integration_commit':head,'branch':branch,'pinned_inputs':[{'commit':x['commit'],'reason':x['reason']} for x in selection['pinned_git_inputs']],'sha256':members},indent=2))
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    for name,digest in members.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
bundle=P/'MoNoTeC-2026-full.bundle'
subprocess.run(['git','-C',str(R),'bundle','create',str(bundle),branch],check=True)
bare=P/'build/bundle-validation.git'
subprocess.run(['git','init','--bare',str(bare)],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','-C',str(bare),'bundle','verify',str(bundle)],check=True)
DEST.mkdir(parents=True)
top=['MoNoTeC-2026-paper.pdf','MoNoTeC-2026-paper.docx','reviewer-response.pdf','reviewer-response.docx','reviewer-response.md','AUTHOR-HANDOFF.md','README.md','EVIDENCE-INDEX.md','MoNoTeC-2026-source.zip','MoNoTeC-2026-full.bundle']
for name in top:shutil.copy2(P/name,DEST/name)
# A ready-to-build TeX tree for readers who do not want to unpack the larger evidence ZIP.
paper_paths=['levels_tex/samplepaper.tex','monotec2026.bib']
paper_paths += [x for x in paths if x.startswith('evidence/integration/20261003-submission/') and ('/sources/' in x or '/figures/' in x or '/checks/' in x or x.endswith('/README.md'))]
paper_paths += ['evidence/instantiation/uav-service-completion-candidate/model.xml']
for name in sorted(set(paper_paths)):
    target=DEST/'paper-source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,target)
release={'integration_commit':head,'branch':branch,'branch_location':'local; full self-contained Git bundle supplied','repository':'https://github.com/artmus208/uppaal_sdn_isac','integration_issue':92,'source_zip_file_count':len(members)+1,'zip_crc_and_sha256_verification':'passed','git_bundle_verified_in_empty_repository':True,'files':{name:hashlib.sha256((DEST/name).read_bytes()).hexdigest() for name in top}}
(DEST/'RELEASE.json').write_text(json.dumps(release,indent=2),encoding='utf-8')
for name in top:assert (DEST/name).read_bytes()==(P/name).read_bytes()
print(json.dumps({'destination':str(DEST),'head':head,'branch':branch,'files':len(members)+1,'zip_bytes':zip_path.stat().st_size,'bundle_bytes':bundle.stat().st_size}))
