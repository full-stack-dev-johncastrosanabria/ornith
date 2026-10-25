"""Wait for the GGUF controller, then run the isolated official-core experiment."""
import argparse,datetime,json,os,pathlib,subprocess,sys,time
from server import ROOT,STATE,active,stop
from memory import require_space

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--after-pid',required=True,type=int);a=ap.parse_args()
    while True:
        command=subprocess.run(['ps','-p',str(a.after_pid),'-o','command='],capture_output=True,text=True).stdout
        if not any(str(ROOT/'scripts'/name) in command for name in ['campaign_gguf.sh','campaign.py']):break
        time.sleep(10)
    require_space()
    if STATE.exists():raise RuntimeError('Prior server state remains; inspect before starting official experiment')
    active()
    lock=ROOT/'logs/campaign.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    stamp=datetime.datetime.now().strftime('%Y%m%dT%H%M%S');checkpoint=ROOT/f'logs/official-campaign-{stamp}.json'
    d={'classification':'official core with local F7/macOS adapters','pid':os.getpid(),'status':'running','stages':[]}
    def save():checkpoint.write_text(json.dumps(d,indent=2)+'\n')
    py=str(ROOT/'harness2/.venv/bin/python');started=False
    try:
        for name,cmd in [('setup',[py,'scripts/setup_harness_official.py']),('preflight',[py,'scripts/harness_official.py','--preflight']),('start',[py,'scripts/server.py','start','mlx']),('api',[py,'scripts/smoke_api.py']),('official-core',[py,'scripts/harness_official.py'])]:
            row={'name':name,'status':'running','started':time.time()};d['stages'].append(row);save()
            with (ROOT/f'logs/official-{name}.log').open('w') as log:p=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            row.update({'rc':p.returncode,'wall_s':time.time()-row['started'],'status':'finished' if p.returncode==0 else 'failed'});save()
            if p.returncode:raise RuntimeError(f'{name} failed rc={p.returncode}; inspect logs/official-{name}.log')
            if name=='start':started=True
        d['status']='stages_finished'
    except BaseException as e:
        d['status']='incomplete';d['error']=str(e);raise
    finally:
        if started and STATE.exists():stop()
        save();lock.unlink(missing_ok=True)
if __name__=='__main__':main()
