"""Resumable native campaign; one worker, detached controller, durable checkpoints."""
import argparse,datetime,json,os,pathlib,subprocess,sys,time
from server import ROOT,STATE,start,stop

def existing_tasks(kind,label):
    found={}
    for path in sorted((ROOT/'benchmarks/results').glob(f'tasks-{kind}-{label}-*.json')):
        for row in json.loads(path.read_text()).get('rows',[]):found[row['task']]=row
    return found

def ensure(kind):
    if STATE.exists():stop()
    start(kind)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--background',action='store_true');a=ap.parse_args()
    process_file=ROOT/'logs/campaign-process.json'
    if a.background:
        if process_file.exists():
            old=json.loads(process_file.read_text());cmd=subprocess.run(['ps','-p',str(old['pid']),'-o','command='],capture_output=True,text=True).stdout
            if str(ROOT/'scripts/campaign.py') in cmd:raise RuntimeError('Owned campaign already running; use status.py.')
        log=ROOT/'logs/campaign-controller.log'
        with log.open('ab') as output:
            child=subprocess.Popen([sys.executable,str(ROOT/'scripts/campaign.py')],cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
        process_file.write_text(json.dumps({'pid':child.pid,'script':str(ROOT/'scripts/campaign.py'),'started':time.time()},indent=2)+'\n');print(f'Native campaign PID {child.pid}; checkpoints in logs/campaign-*.json');return
    lock=ROOT/'logs/campaign.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    process_file.write_text(json.dumps({'pid':os.getpid(),'script':str(ROOT/'scripts/campaign.py'),'started':time.time()},indent=2)+'\n')
    now=datetime.datetime.now().strftime('%Y%m%dT%H%M%S');checkpoint=ROOT/f'logs/campaign-{now}.json'
    data={'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'profile':json.loads((ROOT/'runtimes/profile.json').read_text()),'stages':[],'status':'running'}
    py=str(ROOT/'harness2/.venv/bin/python');mlxpy=str(ROOT/'runtimes/mlx/.venv/bin/python')
    def save():checkpoint.write_text(json.dumps(data,indent=2)+'\n')
    def stage(name,cmd,model=None):
        row={'name':name,'started':time.time(),'command':cmd,'status':'running'};data['stages'].append(row);save();print(name,flush=True);t=time.perf_counter()
        try:
            if model:ensure(model)
            elif name in ['stop-before-direct','stop-final']:stop()
            with (ROOT/f'logs/campaign-{name}.log').open('w') as log:
                p=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT) if cmd else None
            row['rc']=p.returncode if p else 0;row['status']='finished' if row['rc']==0 else 'failed'
            if row['rc']==75:row['status']='resource_blocked';raise SystemExit(75)
        except SystemExit as e:row['rc']=e.code;row['status']='resource_blocked' if e.code==75 else 'interrupted';raise
        except Exception as e:row['status']='infrastructure';row['error']=str(e)
        finally:row['wall_s']=time.perf_counter()-t;save()
    try:
        save()
        remaining=[t for t in ['F7-A','F7-B','F7-C','F7-D'] if t not in existing_tasks('mlx','control')]
        if remaining:stage('mlx-control-remaining',[py,'scripts/bench_tasks.py','--tasks',*remaining],model='mlx')
        compositions=[json.loads(p.read_text()) for p in sorted((ROOT/'benchmarks/results').glob('harness-local-*.json'))]
        valid=bool(compositions and compositions[-1].get('composition',{}).get('valid') and compositions[-1].get('optimization_wall_s'))
        if not valid:stage('local-ppc',[py,'scripts/harness_local.py'],model='mlx')
        guidance=ROOT/'opencode/agents/optimized-guidance.txt'
        compositions=[json.loads(p.read_text()) for p in sorted((ROOT/'benchmarks/results').glob('harness-local-*.json'))]
        valid=bool(compositions and compositions[-1].get('composition',{}).get('valid') and compositions[-1].get('optimization_wall_s') and guidance.exists() and guidance.read_text().strip()==compositions[-1]['composition']['guidance'].strip())
        remaining=[t for t in ['F7-A','F7-B','F7-C','F7-D'] if t not in existing_tasks('mlx','optimized')]
        if remaining and valid:stage('mlx-optimized',[py,'scripts/bench_tasks.py','--tasks',*remaining,'--label','optimized','--harness',str(guidance)],model='mlx')
        elif remaining:data['stages'].append({'name':'mlx-optimized','status':'skipped: no validated frozen composition'});save()
        stage('stop-before-direct',[])
        if not list((ROOT/'benchmarks/results').glob('micro-mlx-direct-*.json')):stage('mlx-direct',[mlxpy,'scripts/bench_mlx.py'])
        # The historical 8K micro is retained separately; obtain a final-profile baseline.
        finals=[json.loads(p.read_text()) for p in (ROOT/'benchmarks/results').glob('micro-bonsai-*.json')]
        if not any(d.get('server',{}).get('profile',{}).get('context')==data['profile']['context'] for d in finals):stage('bonsai-micro',[py,'scripts/bench_api.py'],model='bonsai')
        remaining=[t for t in ['F7-A','F7-B','F7-C','F7-D'] if t not in existing_tasks('bonsai','control')]
        if remaining:stage('bonsai-control',[py,'scripts/bench_tasks.py','--tasks',*remaining],model='bonsai')
        stage('stop-final',[])
        stage('report',[py,'scripts/report.py'])
        data['status']='stages_finished_with_errors' if any(s['status'] not in ['finished'] for s in data['stages']) else 'stages_finished'
    except SystemExit as e:
        data['status']='resource_blocked' if e.code==75 else 'interrupted'
        if e.code==75 and STATE.exists():stop()
        raise
    finally:
        save();lock.unlink(missing_ok=True)
if __name__=='__main__':main()
