"""D030 model-selection cohort: one candidate at a time on global OpenCode, label oc226-control.

Per kind: fetch pinned weights, start, API smoke, agent smoke 3/3 (hard gate: failure is
integration N/E, F7 is not run), micro bench, F7 A-D, stop, MLX direct bench. Resumable:
completed F7 tasks are skipped. Measured candidates in EVICT are removed afterwards to keep
the 8 GiB reserve; their manifests keep the pins for re-download.
"""
import argparse,datetime,json,os,pathlib,shutil,subprocess,sys,time
from server import ROOT,STATE,MLX_MODELS,start,stop
from campaign import existing_tasks

LABEL='oc226-control'
TASKS=['F7-A','F7-B','F7-C','F7-D']
PY=str(ROOT/'harness2/.venv/bin/python');MLXPY=str(ROOT/'runtimes/mlx/.venv/bin/python')
FETCH={'gguf':['/bin/zsh','scripts/setup_gguf.sh'],'qwen':[MLXPY,'scripts/download_model.py','--candidate','qwen'],
       'bonsai9':[MLXPY,'scripts/download_model.py','--candidate','bonsai9'],'granite':[MLXPY,'scripts/download_model.py','--candidate','granite']}
LINKS={'gguf':'ornith-gguf.gguf','qwen':'qwen3.5-9b-mlx','bonsai9':'bonsai2-9b.gguf','granite':'granite-4.1-8b-mlx'}
EVICT={'qwen','bonsai9','granite'}

def evict(kind):
    link=ROOT/'models'/LINKS[kind];target=link.resolve()
    repo=next(p for p in [target,*target.parents] if p.name.startswith('models--'))
    assert repo.parent==(pathlib.Path.home()/'.cache/huggingface/hub').resolve(),repo
    shutil.rmtree(repo);link.unlink()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('kinds',nargs='+',choices=['gguf','qwen','bonsai9','granite','bonsai','mlx']);a=ap.parse_args()
    lock=ROOT/'logs/campaign.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    checkpoint=ROOT/f"logs/campaign-models-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    data={'protocol':'D030','label':LABEL,'pid':os.getpid(),'profile':json.loads((ROOT/'runtimes/profile.json').read_text()),'stages':[],'status':'running'}
    def save():checkpoint.write_text(json.dumps(data,indent=2)+'\n')
    def stage(kind,name,cmd):
        row={'kind':kind,'name':name,'command':cmd,'started':time.time(),'status':'running'};data['stages'].append(row);save();print(kind,name,flush=True)
        with (ROOT/f'logs/campaign-models-{kind}-{name}.log').open('w') as log:p=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        row.update({'rc':p.returncode,'wall_s':time.time()-row['started'],'status':'finished' if p.returncode==0 else 'failed'});save()
        if p.returncode==75:raise SystemExit(75)
        return p.returncode==0
    try:
        for kind in a.kinds:
            if kind in FETCH and not (ROOT/'models'/LINKS[kind]).exists() and not stage(kind,'fetch',FETCH[kind]):continue
            try:
                if STATE.exists():stop()
                start(kind)
            except Exception as e:
                data['stages'].append({'kind':kind,'name':'start','status':'infrastructure','error':str(e)});save();continue
            ok=stage(kind,'smoke-api',[PY,'scripts/smoke_api.py']) and stage(kind,'smoke-agent',[PY,'scripts/smoke_agent.py'])
            if not ok:data['stages'].append({'kind':kind,'name':'f7','status':'not run: smoke gate failed (integration N/E)'});save()
            else:
                stage(kind,'micro',[PY,'scripts/bench_api.py','--label',LABEL])
                remaining=[t for t in TASKS if t not in existing_tasks(kind,LABEL)]
                if remaining:stage(kind,'f7',[PY,'scripts/bench_tasks.py','--tasks',*remaining,'--label',LABEL])
            stop()
            if ok and kind in MLX_MODELS:stage(kind,'direct',[MLXPY,'scripts/bench_mlx.py','--kind',kind])
            if kind in EVICT and len(existing_tasks(kind,LABEL))==len(TASKS):evict(kind);data['stages'].append({'kind':kind,'name':'evict','status':'finished'});save()
        data['status']='stages_finished'
    except SystemExit as e:
        data['status']='resource_blocked' if e.code==75 else 'interrupted';raise
    finally:
        if STATE.exists():stop()
        save();lock.unlink(missing_ok=True)
if __name__=='__main__':main()
