"""Fresh F7 runs with protected public tests and independent external acceptance."""
import argparse,datetime,hashlib,json,os,pathlib,shutil,subprocess,time,uuid
from memory import snapshot
from opencode_local import run,prepare
ROOT=pathlib.Path(__file__).resolve().parents[1]

def hashes(work):
    return {str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (work/'tests').rglob('*') if p.is_file() and not any(t in p.parts for t in ['bin','obj','__pycache__'])}
def grade(work,command):
    env,profile,_,state=prepare(work,'mlx','unused')
    env['PYTHONPATH']=str(work)
    t=time.perf_counter()
    try:
        p=subprocess.run(['/usr/bin/sandbox-exec','-f',str(profile),*__import__('shlex').split(command)],cwd=work,env=env,capture_output=True,text=True,timeout=180)
        return {'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'wall_s':time.perf_counter()-t,'isolation':'native sandbox, independent grading state'}
    except subprocess.TimeoutExpired as e:return {'rc':124,'stdout':str(e.stdout),'stderr':'external grader timeout','wall_s':time.perf_counter()-t}

def task(task_id,s,harness='',label='control',timeout=1200):
    fixture=ROOT/'benchmarks/fixtures'/task_id
    manifest=json.loads((ROOT/'benchmarks/fixtures/manifest.json').read_text());spec=next(t for t in manifest['tasks'] if t['task']==task_id)
    work=ROOT/'benchmarks/work'/f"{s['kind']}-{label}-{task_id}-{uuid.uuid4().hex[:8]}";shutil.copytree(fixture,work)
    # Dependencies restored by the trusted orchestrator before any local-model execution.
    if task_id=='F7-A':
        p=subprocess.run(['dotnet','restore','tests/Acceptance.csproj','--source',str(pathlib.Path.home()/'.nuget/packages'),'-p:NuGetAudit=false'],cwd=work,capture_output=True,text=True,timeout=240)
        if p.returncode:return {'task':task_id,'status':'infrastructure','restore':p.stdout+p.stderr,'workspace':str(work)}
    before_hashes=hashes(work);baseline=grade(work,spec['command'])
    if task_id=='F7-A':
        # Preflight compilation must not pollute the model's initially clean task
        # with hundreds of generated files. Keep only restored NuGet assets.
        for part in ['src','tests']:
            shutil.rmtree(work/part/'bin',ignore_errors=True)
            shutil.rmtree(work/part/'obj/Debug',ignore_errors=True)
    memory=snapshot()
    result=run(work,(work/'TASK.md').read_text(),s['kind'],s['model_id'],harness,timeout=timeout)
    if result.get('resource_abort'):
        from server import stop
        stop()
    final=grade(work,spec['command']);unchanged=before_hashes==hashes(work)
    tools=[e for e in result['events'] if e.get('type')=='tool_use'];finished=[e.get('part',{}) for e in result['events'] if e.get('type')=='step_finish']
    first_tool_s=None
    if tools:
        starts=[e['timestamp'] for e in result['events'] if e.get('type')=='step_start']
        if starts:first_tool_s=(tools[0]['timestamp']-min(starts))/1000
    errors=[e for e in result['events'] if e.get('type')=='error']
    if result.get('resource_abort'):
        return {'task':task_id,'label':label,'status':'infrastructure','artifact_acceptance':final['rc']==0 and unchanged,'acceptance':final,'tests_unchanged':unchanged,'agent':result,'resource_abort':result['resource_abort'],'workspace':str(work)}
    infrastructure=not result['events'] or any(e.get('error',{}).get('name') in ['APIError','ProviderModelNotFoundError','ContextOverflowError'] for e in errors)
    status='pass' if final['rc']==0 and unchanged and not result['timeout'] else ('infrastructure' if infrastructure else 'fail')
    launch_tool_s=(tools[0]['timestamp']-result['started_epoch_ms'])/1000 if tools and 'started_epoch_ms' in result else None
    row={'task':task_id,'label':label,'status':status,'server_at_start':dict(s),'workspace':str(work),'baseline':baseline,'acceptance':final,'artifact_acceptance':final['rc']==0 and unchanged,'tests_unchanged':unchanged,'memory_before':memory,'memory_after':snapshot(),'agent':result,'tool_count':len(tools),'tool_errors':sum(e.get('part',{}).get('state',{}).get('status')=='error' for e in tools),'first_tool_from_launch_s':launch_tool_s,'first_tool_after_step_start_s':first_tool_s,'tokens':[x.get('tokens') for x in finished]}
    if result['timeout']:
        # A disconnected client is not proof that native generation stopped.
        # Restart only our owned model before another task, keeping all parameters.
        from server import stop,start
        recovery=time.perf_counter();stop();start(s['kind'])
        row['timeout_recovery']={'server_restarted':True,'wall_s':time.perf_counter()-recovery,'included_in_agent_wall':False}
    return row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tasks',nargs='+',default=['F7-A','F7-B','F7-C','F7-D']);ap.add_argument('--harness',type=pathlib.Path);ap.add_argument('--label',default='control');ap.add_argument('--timeout',type=int,default=1200);a=ap.parse_args()
    s=json.loads((ROOT/'logs/server.json').read_text());guidance=a.harness.read_text() if a.harness else ''
    out={'schema':1,'server':s,'label':a.label,'harness':guidance,'rows':[],'started':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    p=ROOT/'benchmarks/results'/f"tasks-{s['kind']}-{a.label}-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    for t in a.tasks:
        s=json.loads((ROOT/'logs/server.json').read_text())
        row=task(t,s,guidance,a.label,a.timeout);out['rows'].append(row);p.write_text(json.dumps(out,indent=2)+'\n');print(t,row['status'],row.get('agent',{}).get('wall_s'),p,flush=True)
        if row.get('resource_abort'):raise SystemExit(75)
if __name__=='__main__':main()
