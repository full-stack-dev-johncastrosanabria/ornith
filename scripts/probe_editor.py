"""D039 diagnostic: one Harness² editor call (the stored inv1 mission) with raised editor budget.

Reuses the exact pinned source executor and sandbox. Steps come from LAB_AGENT_STEPS (default 12, so solver runs are
unchanged). Abort rule: >= ABORT_STEPS finished steps with zero edit/write calls => stop and record N/E for editor capability.
"""
import argparse,datetime,hashlib,json,os,pathlib,shutil,signal,threading,time,uuid
import harness_official as h
from opencode_local import ROOT
from server import STATE

RUN=ROOT/'harness2/official/runs/20261108T134833'
PROMPT='Read MISSION.md and follow it. Edit context/harness in place when requested. Save the requested final response verbatim to output/answer.md and return it.'

def events(state):
    out=[]
    try:lines=(state/'stdout.jsonl').read_text().splitlines()
    except FileNotFoundError:return out
    for line in lines:
        try:out.append(json.loads(line))
        except json.JSONDecodeError:pass
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--steps',type=int,default=40);ap.add_argument('--wall',type=int,default=1800);ap.add_argument('--abort-steps',type=int,default=15);a=ap.parse_args()
    h.configure();s=json.loads(STATE.read_text())
    if s['kind']!='mlx':raise SystemExit('Start Ornith MLX alone first')
    work=ROOT/'benchmarks/work'/('probe-editor-'+uuid.uuid4().hex[:10]);work.mkdir(parents=True)
    pristine=RUN/'runs/f7-native-local-oc-seq1/DEV/context/inv1'
    shutil.copytree(pristine,work/'context')
    shutil.copy2(next((RUN/'editor').glob('inv1.a1.*.mission.md')),work/'MISSION.md');(work/'output').mkdir()
    os.environ['LAB_AGENT_STEPS']=str(a.steps)
    started=time.time();abort=[];seen=set(pathlib.Path(p) for p in (ROOT/'opencode/state').iterdir())
    def watch():
        state=None
        while not done.is_set():
            if state is None:
                new=[p for p in (ROOT/'opencode/state').iterdir() if p not in seen and (p/'process.json').exists()]
                state=new[0] if new else None
            else:
                ev=events(state);steps=sum(e.get('type')=='step_finish' for e in ev)
                edits=sum(e.get('type')=='tool_use' and e['part'].get('tool') in ('edit','write') for e in ev)
                if steps>=a.abort_steps and not edits:
                    abort.append(f'{steps} steps, no edit/write call');os.killpg(json.loads((state/'process.json').read_text())['pgid'],signal.SIGTERM);return
            done.wait(15)
    done=threading.Event();threading.Thread(target=watch,daemon=True).start()
    try:result=h.source_run(work,PROMPT,s['kind'],s['model_id'],timeout=a.wall)
    finally:done.set()
    ev=result['events'];steps=[e['part'] for e in ev if e.get('type')=='step_finish']
    tools=[e['part'] for e in ev if e.get('type')=='tool_use']
    changed=[str(p.relative_to(work/'context/harness')) for p in (work/'context/harness').rglob('*') if p.is_file() and (not (pristine/'harness'/p.relative_to(work/'context/harness')).exists() or p.read_bytes()!=(pristine/'harness'/p.relative_to(work/'context/harness')).read_bytes())]
    out={'schema':1,'decision':'D039','steps_cap':a.steps,'wall_cap_s':a.wall,'abort_rule':f'>= {a.abort_steps} steps without edit/write','aborted':abort,'wall_s':result['wall_s'],'timeout':result['timeout'],'rc':result['rc'],
         'steps_finished':len(steps),'last_reason':steps[-1].get('reason') if steps else None,'tool_counts':{t:sum(x.get('tool')==t for x in tools) for t in {x.get('tool') for x in tools}},
         'edit_or_write_calls':sum(x.get('tool') in ('edit','write') for x in tools),'harness_files_changed':changed,
         'per_step_tokens':[{'input':x['tokens'].get('input',0),'cache_read':x['tokens'].get('cache',{}).get('read',0),'output':x['tokens'].get('output',0),'reasoning':x['tokens'].get('reasoning',0)} for x in steps],
         'max_step_context':max((x['tokens'].get('input',0)+x['tokens'].get('cache',{}).get('read',0)+x['tokens'].get('output',0) for x in steps),default=None),
         'errors':[e.get('error') for e in ev if e.get('type')=='error'],'answer_written':(work/'output/answer.md').exists(),'workspace':str(work),'state':result['state'],'started_utc':datetime.datetime.utcfromtimestamp(started).isoformat()+'Z'}
    p=ROOT/'benchmarks/results'/f"probe-editor-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.json";p.write_text(json.dumps(out,indent=2)+'\n');print(p);print(json.dumps({k:v for k,v in out.items() if k!='per_step_tokens'},indent=2))
if __name__=='__main__':main()
