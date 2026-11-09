"""D030 model-selection cohort: one candidate at a time on global OpenCode, label oc226-nodocker.

Per kind: fetch pinned weights, start, API smoke, agent smoke 3/3 (hard gate: failure is
integration N/E, F7 is not run), micro bench, F7 A-D, stop, MLX direct bench. Resumable:
completed F7 tasks are skipped. Measured candidates in EVICT are removed afterwards to keep
the 8 GiB reserve; their manifests keep the pins for re-download.
"""
import argparse,datetime,json,os,pathlib,shutil,subprocess,sys,time
from server import ROOT,STATE,MLX_MODELS,VENDOR_SAMPLING,start,stop,load_profile
from campaign import existing_tasks
from score_models import length_steps

# Docker Desktop was closed mid-session; every candidate, Ornith MLX included, reruns under that host state.
LABEL=os.environ.get('LAB_LABEL','oc226-nodocker')  # D049: the D031 repeat cohort runs under its own label
TASKS=['F7-A','F7-B','F7-C','F7-D']
PY=str(ROOT/'harness2/.venv/bin/python');MLXPY=str(ROOT/'runtimes/mlx/.venv/bin/python')
FETCH={'mlx':[MLXPY,'scripts/download_model.py'],'gguf':['/bin/zsh','scripts/setup_gguf.sh'],'qwen':[MLXPY,'scripts/download_model.py','--candidate','qwen'],
       'bonsai9':[MLXPY,'scripts/download_model.py','--candidate','bonsai9'],'granite':[MLXPY,'scripts/download_model.py','--candidate','granite'],
       'gemma':[MLXPY,'scripts/download_model.py','--candidate','gemma'],'sera8':[MLXPY,'scripts/download_model.py','--candidate','sera8']}
LINKS={'mlx':'ornith-mlx','gguf':'ornith-gguf.gguf','qwen':'qwen3.5-9b-mlx','bonsai9':'bonsai2-9b.gguf','granite':'granite-4.1-8b-mlx','gemma':'gemma-4-12b-mlx','sera8':'sera-8b.gguf'}
KEEP={'gguf'}  # D053: the D050 winner stays on disk for daily OpenCode use
EVICT={'mlx','qwen','bonsai9','granite','gemma','sera8'}
# D035/D036: Gemma's template defaults to enable_thinking=false, so its reasoning arm turns thinking on instead.
THINKING_OFF_BY_DEFAULT={'gemma'}

def reasoning_arm(kind,primary):
    """Mechanical secondary arm: 'on' for thinking-off-by-default models (D036), 'off' after a cap hit (D032)."""
    if len(primary)!=len(TASKS):return None
    if kind in THINKING_OFF_BY_DEFAULT:return 'on'
    return 'off' if any(length_steps(r) for r in primary.values()) else None
COOLDOWN_S=300

def evict(kind):
    link=ROOT/'models'/LINKS[kind];hub=(pathlib.Path.home()/'.cache/huggingface/hub').resolve()
    # D046: follow one hop only; the shared-blob hub layout symlinks repo blobs into hub/blobs, where the weights live.
    first=pathlib.Path(os.path.normpath(link.parent/os.readlink(link)))
    repo=next(p for p in [first,*first.parents] if p.name.startswith('models--'))
    assert repo.parent.resolve()==hub,repo
    blobs=lambda r:{b.resolve() for b in (r/'blobs').glob('*') if b.is_symlink()}
    shared=set().union(*(blobs(r) for r in hub.glob('models--*') if r.name!=repo.name))
    for b in blobs(repo)-shared:
        if hub/'blobs' in b.parents:b.unlink()
    shutil.rmtree(repo);link.unlink()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('kinds',nargs='+',choices=['gguf','qwen','bonsai9','granite','bonsai','mlx','gemma','sera8']);a=ap.parse_args()
    lock=ROOT/'logs/campaign.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    checkpoint=ROOT/f"logs/campaign-models-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    data={'protocol':'D030','label':LABEL,'pid':os.getpid(),'profile':load_profile(),'stages':[],'status':'running'}
    data['docker_vm_running_at_start']=bool(subprocess.run(['pgrep','-f','Virtualization.VirtualMachine'],capture_output=True).stdout)
    def save():checkpoint.write_text(json.dumps(data,indent=2)+'\n')
    def stage(kind,name,cmd):
        row={'kind':kind,'name':name,'command':cmd,'started':time.time(),'status':'running'};data['stages'].append(row);save();print(kind,name,flush=True)
        with (ROOT/f'logs/campaign-models-{kind}-{name}.log').open('w') as log:p=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        row.update({'rc':p.returncode,'wall_s':time.time()-row['started'],'status':'finished' if p.returncode==0 else 'failed'});save()
        if p.returncode==75:raise SystemExit(75)
        return p.returncode==0
    try:
        for i,kind in enumerate(a.kinds):
            # D043 operator pause: `touch logs/campaign.pause` stops the campaign cleanly before the next model.
            if (ROOT/'logs/campaign.pause').exists():data.update(status='paused',remaining=a.kinds[i:]);save();return
            # Fanless Air: idle cooldown before every model, the first of a resumed run included, so run order and
            # pause-time use do not bias speed; host state is recorded per model, not only at campaign start.
            time.sleep(COOLDOWN_S)
            data['stages'].append({'kind':kind,'name':'thermal','cooldown_s':COOLDOWN_S,'pmset_therm':subprocess.run(['pmset','-g','therm'],capture_output=True,text=True).stdout.strip(),
                                   'docker_vm_running':bool(subprocess.run(['pgrep','-f','Virtualization.VirtualMachine'],capture_output=True).stdout),'loadavg':os.getloadavg()});save()
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
            if (ROOT/'logs/campaign.pause').exists():data.update(status='paused',remaining=a.kinds[i:],paused_before=f'{kind} reasoning arm');save();return
            mode=reasoning_arm(kind,existing_tasks(kind,LABEL)) if ok and LABEL=='oc226-nodocker' else None  # D049: repeats are primary-arm only
            if mode:
                # D036: a thinking-on arm uses the publisher's recommended sampling when one is pinned.
                vendor=mode=='on' and kind in VENDOR_SAMPLING
                tag='vendor' if vendor else {'off':'nothink','on':'think'}[mode];os.environ['LAB_THINKING']=mode
                if vendor:os.environ['LAB_SAMPLING']='vendor'
                try:
                    start(kind)
                    if stage(kind,f'{tag}-smoke-agent',[PY,'scripts/smoke_agent.py']):
                        remaining=[t for t in TASKS if t not in existing_tasks(kind,f'{LABEL}-{tag}')]
                        if remaining:stage(kind,f'{tag}-f7',[PY,'scripts/bench_tasks.py','--tasks',*remaining,'--label',f'{LABEL}-{tag}'])
                    else:data['stages'].append({'kind':kind,'name':f'{tag}-f7','status':'not run: smoke gate failed (integration N/E)'});save()
                finally:
                    os.environ.pop('LAB_THINKING',None);os.environ.pop('LAB_SAMPLING',None)
                    if STATE.exists():stop()
            if kind in EVICT and len(existing_tasks(kind,LABEL))==len(TASKS):evict(kind);data['stages'].append({'kind':kind,'name':'evict','status':'finished'});save()
        data['status']='stages_finished'
    except SystemExit as e:
        data['status']='resource_blocked' if e.code==75 else 'interrupted';raise
    finally:
        if STATE.exists():stop()
        save();lock.unlink(missing_ok=True)
if __name__=='__main__':main()
