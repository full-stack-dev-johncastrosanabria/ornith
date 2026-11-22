"""D060/D061: Harness² with a fixed Claude editor, one arm per oc232 model.

Reported as "cloud-assisted optimization, local inference", never as official or local-only Harness².
Run with harness2/.venv/bin/python (the official core is imported). Commands:
  capture KIND             official core runs DEV with KIND as solver on the global OpenCode; the first editor call
                           (INV) is saved verbatim and the core stops. No local editor runs.
  bundle KIND              verbatim editor input (D041 header + D042 generality rule), delivered by one Read
  ingest KIND TRANSCRIPT   D041 audit, always-on edits only, DEV-string hard gate, frozen guidance
  evaluate KIND            smoke gate, DEV once (recorded only), the label's task set with the frozen guidance
  report                   per-model comparison against the same model's oc232-nodocker control
"""
import argparse,dataclasses,datetime,json,os,pathlib,re,shutil,subprocess,sys,time
from unittest.mock import patch
import bench_tasks,harness_official as h
from cloud_editor_arm import ALWAYS_ON,EDITOR_HEADER,blocks,parse,scan,sha,text_of
from opencode_local import ROOT,configuration
from server import STATE,start,stop
from harness2.core import recursion
from harness2.core.proposer import Proposer
from harness2.core.schedule import run_domain

OUT=ROOT/'harness2/h2claude'
CONTROL,TREATMENT='oc232-nodocker','oc232-nodocker-h2claude'
KINDS=('gguf','bonsai','bonsai9','gptoss')
# D042 lesson, pre-registered in D060: held-out workspaces differ from DEV.
HEADER=EDITOR_HEADER+'\n- The always-on files are injected into every future task, whose workspaces differ from this one. Keep them general: never name files, functions, identifiers or literal values of any workspace.'
PY=str(ROOT/'benchmarks/.venv/bin/python')
from score_models import protocol
os.environ['LAB_AGENT_STEPS']=str(protocol(TREATMENT)['steps'])  # D061: same step budget as the control cohort

class Captured(BaseException):
    """Escapes Proposer.call and run_domain, which catch Exception only."""

class CaptureProposer(Proposer):
    """Saves the first editor call verbatim (MISSION.md exactly as upstream _opencode writes it) and stops the core."""
    def call(self,mission,context_dir,label,*,system='',**kw):
        d=self.capture_dir;shutil.rmtree(d,ignore_errors=True);d.mkdir(parents=True)
        if context_dir and pathlib.Path(context_dir).is_dir():shutil.copytree(context_dir,d/'context')
        (d/'MISSION.md').write_text((f'{system}\n\n---\n\n' if system else '')+mission)
        (d/'call.json').write_text(json.dumps({'label':label,'options':{k:str(v) for k,v in kw.items()},'mission_chars':len(mission),'system_chars':len(system)},indent=2)+'\n')
        raise Captured(label)

class Adapter(h.F7Adapter):
    """The F7/DEV adapter with the model under test as solver and the global OpenCode executor (no source executor)."""
    def __init__(self,root,kind):
        super().__init__(root)
        self.kind=kind;ref=configuration(kind,'')[1]
        self.spec=dataclasses.replace(self.spec,name=f'dev-{kind}',channels={k:dataclasses.replace(v,model=ref) for k,v in self.spec.channels.items()})
    def execute(self,task_id,harness_dir,run_id,*,timeout=None):
        self.task_prompt(task_id)
        out=self.root/'executions'/run_id;out.mkdir(parents=True,exist_ok=True);result=out/'result.json'
        if result.exists():return out
        s=json.loads(STATE.read_text())
        if s['kind']!=self.kind:raise RuntimeError(f"server runs {s['kind']}, not {self.kind}")
        row=bench_tasks.task(task_id,s,h.text_harness(harness_dir or self.base_harness()),label=f'h2claude-dev-{self.kind}',timeout=timeout or protocol(TREATMENT)['timeout'])
        result.write_text(json.dumps(row,indent=2)+'\n')
        if row['status']=='infrastructure' or row.get('timeout_recovery',{}).get('server_restarted') is False:raise RuntimeError('Infrastructure failure: '+str(result))
        return out

def capture(kind):
    if json.loads(STATE.read_text())['kind']!=kind:raise SystemExit(f'Start {kind} alone first')
    root=OUT/kind/datetime.datetime.now().strftime('%Y%m%dT%H%M%S');adapter=Adapter(root,kind)
    prop=CaptureProposer(adapter.spec.channels['proposer'],audit_dir=root/'editor',attempts=1);prop.capture_dir=OUT/kind/'capture'
    t=time.perf_counter()
    try:
        with patch.object(recursion,'run_mode',h.sequential_dispatch):
            run_domain('programming',['DEV'],1,adapter=adapter,prop=prop,runs_root=adapter.spec.runs_root,library_root=root/'library',modes=('seq',))
        raise SystemExit('The core finished without an editor call; nothing captured')
    except Captured as c:
        rollouts=[json.loads(p.read_text()) for p in sorted((root/'executions').rglob('result.json'))]
        meta={'decision':'D060','kind':kind,'call':str(c),'run_root':str(root),'wall_s':time.perf_counter()-t,'steps':os.environ.get('LAB_AGENT_STEPS','12'),
              'dev_rollouts':[{'status':r['status'],'wall_s':r.get('agent',{}).get('wall_s')} for r in rollouts]}
        (OUT/kind/'capture.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2))

def bundle(kind):
    d=OUT/kind;cap=d/'capture'
    files=[('MISSION.md',cap/'MISSION.md')]+[(f'context/{p.relative_to(cap/"context")}',p) for p in sorted((cap/'context').rglob('*')) if p.is_file()]
    text='\n\n'.join([HEADER]+[f'<<<WORKSPACE FILE {name}>>>\n{p.read_text()}\n<<<END>>>' for name,p in files])+'\n'
    prompt=f'Use the Read tool exactly once to read the whole file {d/"input.md"} (no offset or limit), then follow the instructions in that file. Do not call any other tool.'
    (d/'input.md').write_text(text);(d/'prompt.txt').write_text(prompt)
    meta={'kind':kind,'input_sha256':sha(text),'prompt_sha256':sha(prompt),'input_chars':len(text),'files':[n for n,_ in files]}
    (d/'input.json').write_text(json.dumps(meta,indent=2)+'\n');print(d/'prompt.txt',json.dumps(meta))

def audit(kind,msgs,base):
    """D041 audit generalized per model; D060: any gate failure or zero edits is N/E, no rerun."""
    d=OUT/kind;asst=[m for m in msgs if m.get('role')=='assistant']
    uses=[b for m in asst for b in blocks(m) if b.get('type')=='tool_use']
    results=[b for m in msgs if m.get('role')=='user' for b in blocks(m) if b.get('type')=='tool_result']
    args=uses[0].get('input',{}) if uses else {}
    permitted=len(uses)==1 and uses[0].get('name')=='Read' and args.get('file_path')==str(d/'input.md') and not {'offset','limit'}&set(args)
    seen='\n'.join(re.sub(r'^\s*\d+\t','',line,count=1) for line in text_of(results[0]).splitlines()) if results else ''
    final='\n'.join(b['text'] for m in asst for b in blocks(m) if b.get('type')=='text')
    edits,answers,outside,bad=parse(final)
    cand=d/'harness';shutil.rmtree(cand,ignore_errors=True);shutil.copytree(base,cand)
    for rel,content in edits.items():
        if rel in ALWAYS_ON:(cand/rel).write_text(content+'\n' if content else '')
    guidance=h.text_harness(cand);hits,word=scan(guidance)
    a={'decision':'D060','kind':kind,'label':TREATMENT,'models':sorted({m.get('model') for m in asst}-{None}),'tool_calls':[{'name':u.get('name'),'input':u.get('input')} for u in uses],
       'permitted_tools':permitted,'input_delivered_verbatim':(d/'input.md').read_text().strip() in seen,'input_sha256':sha((d/'input.md').read_text()),
       'edited':sorted(edits),'outside_whitelist':bad,'answer_blocks':len(answers),'text_outside_blocks_chars':len(outside),'reject_hits':hits,
       'word_normalize_count':word,'guidance_chars':len(guidance),'guidance_sha256':sha(guidance)}
    a['status']=('N/E: unpermitted tool use' if not permitted else 'N/E: input not delivered verbatim' if not a['input_delivered_verbatim']
                 else 'N/E: malformed output' if bad or len(answers)!=1 else 'N/E: contaminated (DEV-specific strings)' if hits
                 else 'N/E: no edits' if guidance==h.text_harness(base) else 'ok')
    return a,final,answers,guidance

def ingest(kind,transcript):
    d=OUT/kind
    for name in ('harness','frozen-guidance.txt','audit.json','answer.md','output.md','transcript.jsonl'):
        p=d/name;shutil.rmtree(p) if p.is_dir() else p.unlink(missing_ok=True)
    t=d/'transcript.jsonl';shutil.copy2(transcript,t)
    msgs=[o['message'] for o in map(json.loads,filter(str.strip,t.read_text().splitlines())) if isinstance(o.get('message'),dict)]
    a,final,answers,guidance=audit(kind,msgs,d/'capture/context/harness')
    (d/'output.md').write_text(final)
    if answers:(d/'answer.md').write_text(answers[0]+'\n')
    if a['status']=='ok':(d/'frozen-guidance.txt').write_text(guidance)
    (d/'audit.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps({k:v for k,v in a.items() if k!='tool_calls'},indent=2))

def evaluate(kind):
    from campaign import existing_tasks
    from score_models import task_set
    d=OUT/kind;lock=ROOT/'logs/campaign.lock'
    if json.loads((d/'audit.json').read_text())['status']!='ok':raise SystemExit(f'{kind}: no usable frozen guidance (see audit.json); arm is N/E')
    if STATE.exists() or lock.exists():raise SystemExit('A server or campaign is active; refusing to share it')
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    guidance=d/'frozen-guidance.txt';log=lambda name:(ROOT/f'logs/h2claude-{kind}-{name}.log').open('w')
    try:
        time.sleep(300)  # D059 cooldown before every model
        host={'pmset_therm':subprocess.run(['pmset','-g','therm'],capture_output=True,text=True).stdout.strip(),'loadavg':os.getloadavg(),'steps':os.environ.get('LAB_AGENT_STEPS','12'),
              'docker_vm_running':bool(subprocess.run(['pgrep','-f','Virtualization.VirtualMachine'],capture_output=True).stdout)}
        start(kind);s=json.loads(STATE.read_text())
        if subprocess.run([PY,'scripts/smoke_agent.py'],cwd=ROOT,stdout=log('smoke'),stderr=subprocess.STDOUT).returncode:raise SystemExit(f'{kind}: agent smoke gate failed (integration N/E)')
        if not (d/'dev-result.json').exists():
            row=bench_tasks.task('DEV',s,guidance.read_text(),label=f'h2claude-dev-{kind}',timeout=protocol(TREATMENT)['timeout'])
            (d/'dev-result.json').write_text(json.dumps(row,indent=2)+'\n');print('DEV',kind,row['status'],flush=True)
        remaining=[t for t in task_set(TREATMENT) if t not in existing_tasks(kind,TREATMENT)]
        (d/'evaluate-host.json').write_text(json.dumps(host,indent=2)+'\n')
        if remaining:
            rc=subprocess.run([PY,'scripts/bench_tasks.py','--tasks',*remaining,'--label',TREATMENT,'--harness',str(guidance),'--timeout',str(protocol(TREATMENT)['timeout'])],cwd=ROOT,stdout=log('tasks'),stderr=subprocess.STDOUT).returncode
            if rc:raise SystemExit(rc)
    finally:
        if STATE.exists():stop()
        lock.unlink(missing_ok=True)

def verdict(delta,n):
    """D061: with 12 tasks a change of at least 3 end-to-end passes is required; D041's ±2 applied at n=4."""
    k=3 if n>4 else 2
    return 'better' if delta>=k else 'worse' if delta<=-k else f'no detectable difference at n={n}'

def report():
    from score_models import score
    out={'decisions':['D060','D061'],'classification':'cloud-assisted optimization (Claude editor), local inference (global OpenCode 2.3.2)','models':{}}
    for kind in KINDS:
        a=OUT/kind/'audit.json';status=json.loads(a.read_text())['status'] if a.exists() else 'N/E: not run'
        c,t=score(kind,CONTROL),score(kind,TREATMENT)
        row={'editor':status,'control':{k:c[k] for k in ('complete','passes','passes_f7','passes_f8','total_s')},'treatment':{k:t[k] for k in ('complete','passes','passes_f7','passes_f8','total_s')}}
        if status=='ok' and c['complete'] and t['complete']:
            row['delta']=t['passes']-c['passes'];row['delta_f7']=t['passes_f7']-c['passes_f7'];row['delta_f8']=t['passes_f8']-c['passes_f8']
            row['verdict']=verdict(row['delta'],c['of'])
            # D061 amendment: a net zero can hide gains and regressions; report both.
            won={x['task'] for x in t['tasks'] if x['status']=='pass'};before={x['task'] for x in c['tasks'] if x['status']=='pass'}
            row['gained']=sorted(won-before);row['lost']=sorted(before-won)
            # D061 (j), user: a close call (|delta| 2 or 3 at n=12) reruns the long tasks once in both arms; the verdict then uses all 15 runs.
            if abs(row['delta']) in (2,3):
                from score_models import LONG,repeat_passes
                rc,rt=repeat_passes(kind,CONTROL+'-r3',LONG),repeat_passes(kind,TREATMENT+'-r3',LONG)
                row['repeat_r3']={'tasks':LONG,'control':rc,'treatment':rt}
                if rc is None or rt is None:row['verdict']+=' (provisional: r3 repeat pending)'
                else:row['delta_15']=row['delta']+rt-rc;row['verdict']=verdict(row['delta_15'],15)
        else:row['verdict']='N/E'
        dev=OUT/kind/'dev-result.json';row['dev_recorded_only']=json.loads(dev.read_text())['status'] if dev.exists() else None
        out['models'][kind]=row
    p=ROOT/'benchmarks/reports/h2claude-comparison-oc232.json';p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['capture','bundle','ingest','evaluate','report']);ap.add_argument('kind',nargs='?',choices=KINDS)
    ap.add_argument('transcript',nargs='?',type=pathlib.Path);a=ap.parse_args()
    if a.action=='ingest':ingest(a.kind,a.transcript)
    elif a.action=='report':report()
    else:{'capture':capture,'bundle':bundle,'evaluate':evaluate}[a.action](a.kind)
