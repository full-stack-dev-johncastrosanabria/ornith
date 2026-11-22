"""D061: writes fixtures F8-A..H and their reference overlays, then appends the F8 manifest rows.

Reference overlays live in benchmarks/reference (inside the lab root, so no agent or grading sandbox can read them).
F7 and DEV fixtures and their manifest rows are never touched. Deterministic: rerunning rewrites identical files.
"""
import hashlib,json,pathlib,shutil,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from create_fixtures import BASE,ROOT,write
import f8_python as P
import f8_stack as S

PYTEST=str(pathlib.Path.home()/'Developer/ornith/benchmarks/.venv/bin/python')+' -m pytest -q -p no:cacheprovider'
REF=ROOT/'benchmarks/reference'

def main():
    mpath=BASE/'manifest.json';raw=mpath.read_text();m=json.loads(raw)
    assert json.dumps(m,indent=2)+'\n'==raw,'manifest would not round-trip byte-identically'
    keep=[r for r in m['tasks'] if not r['task'].startswith('F8-')]
    dotnet=next(r['command'] for r in keep if r['task']=='F7-A')
    tasks={'F8-A':(P.f8a,PYTEST),'F8-B':(P.f8b,PYTEST),'F8-C':(P.f8c,PYTEST),'F8-D':(S.f8d,S.NODE+' --test tests/tasks.test.ts'),
           'F8-E':(S.f8e,'/bin/sh tests/run.sh'),'F8-F':(S.f8f,PYTEST),'F8-G':(S.f8g,dotnet),'F8-H':(P.f8h,PYTEST)}
    rows=[];refs={}
    for t,(build,command) in tasks.items():
        files,ref,prompt=build()
        assert not any(k.startswith('tests/') for k in ref),t
        for d in (BASE/t,REF/t):shutil.rmtree(d,ignore_errors=True)
        rows.append(write(t,files,prompt,command))
        for name,text in ref.items():
            p=REF/t/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n')
        refs[t]={name:hashlib.sha256((REF/t/name).read_bytes()).hexdigest() for name in sorted(ref)}
        for neg,overlay in S.NEGATIVES.get(t,{}).items():
            shutil.rmtree(REF/f'{t}.{neg}',ignore_errors=True)
            for name,text in overlay.items():
                p=REF/f'{t}.{neg}'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n')
        print(t,len(rows[-1]['files']),'files',sum((BASE/t/n).stat().st_size for n in rows[-1]['files'])//1024,'KiB')
    m['tasks']=keep+rows
    mpath.write_text(json.dumps(m,indent=2)+'\n')
    (REF/'manifest.json').write_text(json.dumps({'protocol':'D061','note':'Reference overlays; never copied into an agent workspace.','tasks':refs},indent=2)+'\n')
    assert json.loads(mpath.read_text())['tasks'][:len(keep)]==keep

if __name__=='__main__':main()
