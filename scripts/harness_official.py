"""Official Harness² core + local F7/macOS adapter. No upstream method replacement.

Optimize DEV only; freeze a composed text harness, then evaluate held-out F7.
The executor is the official pinned OpenCode source checkout, not the global CLI.
"""
import argparse,datetime,json,pathlib,shutil,sys,time,uuid
from unittest.mock import patch
import bench_tasks,smoke_agent
from memory import require_space
from opencode_local import ROOT,run
from server import STATE,start,stop
from harness2 import config
from harness2.core import recursion,tree
from harness2.core.proposer import Proposer
from harness2.core.schedule import run_domain
from harness2.core.spec import BenchPrompts,BenchSpec,ChannelSpec
from harness2.substrate.opencode import OpencodeSubstrate

DEP=ROOT/'harness2/official/dependencies'

def configure():
    config.OPENCODE_DIR=DEP/'opencode'
    config.BUN=DEP/'tools/node_modules/.bin/bun'
    OpencodeSubstrate().preflight()

def source_run(work,prompt,kind,model_id,harness='',timeout=1200):
    if kind!='mlx':raise ValueError('Official adaptation fixes the model to Ornith MLX')
    require_space()
    argv=OpencodeSubstrate().run_argv(prompt,pathlib.Path(work),'ornith-mlx/local',agent='ornith-code')
    result=run(work,prompt,kind,model_id,harness,timeout,argv=argv,read_roots=(DEP,))
    result['executor']='official-pinned-opencode-source'
    if result.get('resource_abort'):stop();raise SystemExit(75)
    return result

def text_harness(directory):
    data=tree.read_tree(OpencodeSubstrate().surface(),pathlib.Path(directory))
    validate_text_tree(data)
    return '\n\n'.join(data.get(name,'') for name in OpencodeSubstrate().surface().always_on).strip()

def validate_text_tree(data):
    allowed=set(OpencodeSubstrate().surface().always_on)
    extra=[k for k,v in data.items() if k not in allowed and v.strip()]
    if extra:raise ValueError('This initial adapter supports always-on text only; remove: '+', '.join(extra))

def sequential_dispatch(mode,*args,**kw):
    if mode!='seq':raise ValueError('Sequential only')
    return recursion.run_sequential(*args,propose_workers=1,rollout_workers=1,**kw)

class LocalProposer(Proposer):
    """Keep upstream call/cache/retry/harvest; replace only the native launch boundary."""
    def _opencode(self,cwd,mission,system,wall):
        work=ROOT/'benchmarks/work'/('official-editor-'+uuid.uuid4().hex[:10])
        shutil.copytree(cwd,work)
        (work/'MISSION.md').write_text((system+'\n\n' if system else '')+mission)
        (work/'output').mkdir(exist_ok=True)
        s=json.loads(STATE.read_text())
        prompt='Read MISSION.md and follow it. Edit context/harness in place when requested. Save the requested final response verbatim to output/answer.md and return it.'
        result=source_run(work,prompt,s['kind'],s['model_id'],timeout=wall)
        # Harvest exactly what upstream expects, before its temporary session ends.
        if (work/'context').exists():shutil.copytree(work/'context',cwd/'context',dirs_exist_ok=True)
        answer=work/'output/answer.md'
        text=answer.read_text() if answer.exists() else '\n'.join(e.get('part',{}).get('text','') for e in result['events'] if e.get('type')=='text')
        if result['timeout']:
            stop();start('mlx')
            return '',0.0,'local source executor timeout'
        errors=[e for e in result['events'] if e.get('type')=='error']
        if errors or result['rc']:return '',0.0,'local source executor failed; evidence at '+result['state']
        return text,0.0,''

class F7Adapter:
    def __init__(self,root):
        self.root=root;self.substrate=OpencodeSubstrate()
        channel=ChannelSpec('opencode','ornith-mlx/local',effort='',steps=12,timeout=600)
        self.spec=BenchSpec(name='f7-native-local',runs_root=root/'runs',install_mode='workspace_config',
            prompts=BenchPrompts(work='make small correct programming changes and verify them locally',
                inv_levers='Edit only always-on text. No scripts, skills, plugins or subagents in this initial run.',
                dom_levers='Guide file reading, focused edits, test execution and concise completion.'),
            channels={'proposer':channel,'selector':channel},leak_globs=('tests/**','**/tests/**'))
        base={k:'' for k in self.substrate.surface().always_on}
        base['systemprompt.md']='Read relevant files, make minimal changes, run tests and report their actual results.\n'
        tree.write_tree(self.substrate.surface(),base,self.base_harness(),stubs=False)
        source=root/'sources/DEV';source.mkdir(parents=True,exist_ok=True)
        for p in (ROOT/'benchmarks/fixtures/DEV').glob('*.py'):shutil.copy2(p,source/p.name)

    def tasks(self,split='all'):return ['DEV']
    def domain_of(self,task_id):return 'programming'
    def task_prompt(self,task_id):
        if task_id!='DEV':raise ValueError('Held-out F7 is never supplied to the optimizer')
        return (ROOT/'benchmarks/fixtures/DEV/TASK.md').read_text()
    def task_files(self,task_id):
        self.task_prompt(task_id)
        return self.root/'sources/DEV'
    def base_harness(self):return self.root/'base'
    def validate_tree(self,data):validate_text_tree(data)
    def execute(self,task_id,harness_dir,run_id,*,timeout=None):
        self.task_prompt(task_id)
        out=self.root/'executions'/run_id;out.mkdir(parents=True,exist_ok=True)
        resultfile=out/'result.json'
        if resultfile.exists():return out
        s=json.loads(STATE.read_text())
        with patch.object(bench_tasks,'run',source_run):
            row=bench_tasks.task(task_id,s,text_harness(harness_dir or self.base_harness()),label='official-dev',timeout=timeout or 600)
        resultfile.write_text(json.dumps(row,indent=2)+'\n')
        if row['status']=='infrastructure':raise RuntimeError('Infrastructure failure: '+str(resultfile))
        return out
    def _row(self,run_dir):return json.loads((run_dir/'result.json').read_text())
    def delivered(self,run_dir):return bool(self.deliverable_files(run_dir))
    def trajectory(self,run_dir,*,obs_trunc):
        row=self._row(run_dir);events=row.get('agent',{}).get('events',[]);lines=[]
        for event in events:
            if event.get('type')=='tool_use':
                p=event['part'];lines.append('[ACTION] '+p.get('tool','')+'\n[OBSERVATION]\n'+json.dumps(p.get('state',{}),ensure_ascii=False))
            elif event.get('type')=='error':lines.append('[ERROR] '+json.dumps(event))
            elif event.get('type')=='text':lines.append('[OBSERVATION] '+event.get('part',{}).get('text',''))
        return '\n\n'.join(lines)
    def deliverable_files(self,run_dir):
        row=self._row(run_dir);work=pathlib.Path(row['workspace']);files={}
        fixture=ROOT/'benchmarks/fixtures/DEV'
        for p in work.glob('*.py'):
            if not (fixture/p.name).exists() or p.read_bytes()!=(fixture/p.name).read_bytes():files[p.name]=p.read_text()
        return files
    def deliverable_text(self,run_dir):return '\n\n'.join(k+'\n'+v for k,v in self.deliverable_files(run_dir).items())
    def score(self,run_dir,task_id):
        row=self._row(run_dir)
        return {'artifact_acceptance':row.get('artifact_acceptance'),'agent_status':row['status']}

def evaluate(label,harness=''):
    for tid in ['F7-A','F7-B','F7-C','F7-D']:
        p=ROOT/'benchmarks/results'/f'tasks-mlx-{label}-{tid}.json'
        if p.exists():continue
        with patch.object(bench_tasks,'run',source_run):
            row=bench_tasks.task(tid,json.loads(STATE.read_text()),harness,label=label)
        p.write_text(json.dumps({'label':label,'executor':'official-pinned-opencode-source','rows':[row]},indent=2)+'\n')
        print(tid,row['status'],flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preflight',action='store_true');a=ap.parse_args()
    configure()
    if a.preflight:print('Official source substrate preflight OK; no model call made.');return
    if json.loads(STATE.read_text())['kind']!='mlx':raise RuntimeError('Start Ornith MLX alone first')
    # Same pinned source executor in smoke, control, probes and held-out treatment.
    with patch.object(smoke_agent,'run',source_run):smoke_agent.main()
    evaluate('official-source-control')
    now=datetime.datetime.now().strftime('%Y%m%dT%H%M%S');root=ROOT/'harness2/official/runs'/now
    adapter=F7Adapter(root);prop=LocalProposer(adapter.spec.channels['proposer'],audit_dir=root/'editor',attempts=1)
    t=time.perf_counter()
    # Upstream sequential exposes worker arguments, but run_domain does not forward
    # them. Inject those arguments at dispatch, leaving its algorithm untouched.
    with patch.object(recursion,'run_mode',sequential_dispatch):
        result=run_domain('programming',['DEV'],1,adapter=adapter,prop=prop,runs_root=adapter.spec.runs_root,library_root=root/'library',modes=('seq',))
    result.update({'classification':'official Harness² core with local macOS/F7/source-launch adapters','optimization_wall_s':time.perf_counter()-t,'editor_calls':len(prop._calls),'root':str(root)})
    output=ROOT/'benchmarks/results'/f'harness-official-local-{now}.json';output.write_text(json.dumps(result,indent=2)+'\n')
    summaries=list((root/'runs').glob('**/summary.json'))
    chosen=[]
    for p in summaries:
        d=json.loads(p.read_text());sel=d.get('selections',{}).get('seq',{})
        if sel.get('ok') and not sel.get('chosen_tree_is_base',True):
            hp=p.parent/'harnesses'/sel['chosen_label']
            if not hp.exists():hp=next((q for q in (root/'runs').glob('**/harnesses/'+sel['chosen_label'])),hp)
            if hp.exists():chosen.append(hp)
    if result['failed'] or len(chosen)!=1:raise RuntimeError('Official run did not produce one validated changed harness; inspect '+str(output))
    guidance=text_harness(chosen[0]);(root/'frozen-guidance.txt').write_text(guidance)
    evaluate('official-source-treatment',guidance)
    comparison={'classification':result['classification'],'optimization_wall_s':result['optimization_wall_s'],'optimization_result':str(output),'conditions':{}}
    for label in ['official-source-control','official-source-treatment']:
        rows=[json.loads(p.read_text())['rows'][0] for p in sorted((ROOT/'benchmarks/results').glob(f'tasks-mlx-{label}-F7-*.json'))]
        comparison['conditions'][label]={'artifact_passes':sum(bool(r.get('artifact_acceptance')) for r in rows),'agent_completions':sum(r['status']=='pass' for r in rows),'n':len(rows),'tasks':[{'task':r['task'],'status':r['status'],'wall_s':r.get('agent',{}).get('wall_s')} for r in rows]}
    (ROOT/'benchmarks/reports/harness-official-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
    print(output,flush=True)
if __name__=='__main__':main()
