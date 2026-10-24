"""Explicit local methodology reproduction, NOT the official Harness² runner.

k=1, sequential, one worker, same fixed local solver/improver/composer.
Only DEV is optimized. F7 holdouts are evaluated by a separate command.
"""
import datetime,json,pathlib,time,urllib.request
from bench_tasks import task
ROOT=pathlib.Path(__file__).resolve().parents[1]

def propose(s,prompt):
    output=json.loads((ROOT/'runtimes/profile.json').read_text())['output']
    body={'model':s['model_id'],'messages':[{'role':'system','content':'Return only a concise system-prompt paragraph for a coding agent. No markdown fences. Do not solve the task or include code. Limit to 100 words. All execution is native macOS, local-only, immutable public tests, no delegation.'},{'role':'user','content':prompt}],'temperature':.6,'top_p':.95,'max_tokens':output}
    req=urllib.request.Request(f"http://127.0.0.1:{s['port']}/v1/chat/completions",data=json.dumps(body).encode(),headers={'Content-Type':'application/json'});t=time.perf_counter()
    with urllib.request.urlopen(req,timeout=600) as r:d=json.load(r)
    text=d['choices'][0]['message'].get('content','').strip()
    if not text or len(text)>4000:raise ValueError('Invalid guidance; retain control harness.')
    return {'wall_s':time.perf_counter()-t,'response':d,'guidance':text}

def trace(row):
    # No external acceptance scores/solutions/rubrics are provided to the editor.
    return {'task':'DEV normalize strings','wall_s':row.get('agent',{}).get('wall_s'),'tools':[{ 'tool':e.get('part',{}).get('tool'),'state':e.get('part',{}).get('state')} for e in row.get('agent',{}).get('events',[]) if e.get('type')=='tool_use']}

def main():
    s=json.loads((ROOT/'logs/server.json').read_text())
    if s['kind']!='mlx':raise RuntimeError('This experiment fixes Ornith MLX for all three roles.')
    label=datetime.datetime.now().strftime('%Y%m%dT%H%M%S');p=ROOT/'benchmarks/results'/f'harness-local-{label}.json'
    out={'method':'local Propose-Probe-Compose reproduction, not official Harness2 model-backed runner','k':1,'mode':'sequential','workers':1,'server':s,'optimization_task':'DEV','holdouts':['F7-A','F7-B','F7-C','F7-D']};t=time.perf_counter()
    def save():p.write_text(json.dumps(out,indent=2)+'\n')
    out['control']=task('DEV',s,label='optimization-control',timeout=600);save();print('control complete',flush=True)
    out['proposal']=propose(s,'Propose ONE change to system/tool guidance based on this execution trace. Preserve all constraints. '+json.dumps(trace(out['control'])));save();print('proposal complete',flush=True)
    out['probe']=task('DEV',s,out['proposal']['guidance'],label='optimization-probe',timeout=600);save();print('probe complete',flush=True)
    out['composition']=propose(s,'Compose the final reusable system guidance from the control/probe contrast. Do not mention task-specific answers. Proposed guidance: '+out['proposal']['guidance']+' Control: '+json.dumps(trace(out['control']))+' Probe: '+json.dumps(trace(out['probe'])));save()
    out['optimization_wall_s']=time.perf_counter()-t;out['guidance_path']='opencode/agents/optimized-guidance.txt'
    (ROOT/out['guidance_path']).write_text(out['composition']['guidance']+'\n');save();print(p,flush=True)
if __name__=='__main__':main()
