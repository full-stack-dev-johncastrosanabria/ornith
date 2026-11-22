"""D062 grader: runs the last fenced block of the expected language of each chat answer against hidden checks in
the bench_tasks sandbox, after the model server is stopped. Usage: grade_chat.py [--selfcheck] [kind ...]"""
import datetime,json,pathlib,re,shutil,statistics,subprocess,sys,uuid
from bench_tasks import grade
from memory_gate import breaches
from opencode_local import WORK
ROOT=pathlib.Path(__file__).resolve().parents[1];CHAT=ROOT/'benchmarks/chat'
PY=str(pathlib.Path.home()/'Developer/ornith/benchmarks/.venv/bin/python')  # space-free path, readable in the sandbox
LANGS={'python':{'python','py','python3'},'csharp':{'csharp','cs','c#'},'sql':{'sql','sqlite'},'text':{'text','txt','plaintext','output','console'}}
NET=f"/bin/sh -c 'dotnet build Check.csproj --no-restore --disable-build-servers -p:UseSharedCompilation=false -nologo -v quiet && dotnet bin/Debug/net10.0/Check.dll'"
# D062 usability bar, pre-registered before any chat result.
BAR_PASS=.75;BAR_MEDIAN_S=180

def block(content,lang):
    blocks=re.findall(r'```[ \t]*([^\n`]*)\n(.*?)```',content or '',re.S)
    ok=[b for l,b in blocks if l.strip().lower() in LANGS[lang]] or [b for l,b in blocks if not l.strip()]
    return ok[-1] if ok else None

def check(task,lang,code,tag):
    if code is None:return False,'no code block'
    if lang=='text':
        norm=lambda s:'\n'.join(l.rstrip() for l in s.strip().splitlines())
        return norm(code)==norm((CHAT/f'checks/{task}.txt').read_text()),code.strip()[:200]
    work=WORK/f'chat-{tag}-{task}-{uuid.uuid4().hex[:8]}';work.mkdir(parents=True)
    if lang=='csharp':
        shutil.copy(CHAT/'checks/Check.csproj',work);shutil.copy(CHAT/f'checks/{task}.cs',work/'Program.cs');(work/'Solution.cs').write_text(code)
        # Trusted restore outside the sandbox (as bench_tasks.restore); no package references, offline source.
        p=subprocess.run(['dotnet','restore','Check.csproj','--source',str(pathlib.Path.home()/'.nuget/packages')],cwd=work,capture_output=True,text=True,timeout=240)
        if p.returncode:return None,'restore failed: '+(p.stdout+p.stderr)[-300:]
        r=grade(work,NET)
    else:
        (work/('query.sql' if lang=='sql' else 'solution.py')).write_text(code);shutil.copy(CHAT/f'checks/{task}.py',work/'check.py')
        r=grade(work,f'{PY} check.py')
    return r['rc']==0 and 'OK' in r['stdout'],(r['stdout']+r['stderr'])[-300:]

def selfcheck():
    cases=json.loads((CHAT/'selfcheck.json').read_text());tasks={t['id']:t['lang'] for t in json.loads((CHAT/'tasks.json').read_text())['tasks']}
    assert set(cases)==set(tasks),set(tasks)^set(cases)
    for task,lang in tasks.items():
        for want,content in [(True,cases[task]['good']),(False,cases[task]['bad'])]:
            got,why=check(task,lang,block(content,lang),'selfcheck');assert got is want,(task,want,why);print(task,'good' if want else 'bad','ok')

def p90(x):return statistics.quantiles(x,n=10)[8] if len(x)>1 else x[0]

def summarize(kind,path,gate):
    data=json.loads(path.read_text());lang={t['id']:t['lang'] for t in json.loads((CHAT/'tasks.json').read_text())['tasks']};rows=[]
    for r in data['rows']:
        if 'error' in r:rows.append({'task':r['task'],'rep':r['rep'],'status':'infrastructure','why':r['error']});continue
        ok,why=check(r['task'],lang[r['task']],block(r['content'],lang[r['task']]),kind)
        trunc=r['finish_reason']=='length'
        tps=(r.get('timings') or {}).get('predicted_per_second') or ((r.get('usage') or {}).get('completion_tokens',0)/(r['wall_s']-r['ttft_s']) if r.get('ttft_s') and r['wall_s']>r['ttft_s'] else None)
        rows.append({'task':r['task'],'rep':r['rep'],'status':'infrastructure' if ok is None else 'pass' if ok and not trunc else 'fail','truncated':trunc,'why':why,
                     'wall_s':r['wall_s'],'ttft_s':r['ttft_s'],'decode_tps':tps,'completion_tokens':(r.get('usage') or {}).get('completion_tokens')})
    measured=[r for r in rows if r['status']!='infrastructure'];passes=sum(r['status']=='pass' for r in measured);walls=[r['wall_s'] for r in measured]
    try:import score_models;cohort=score_models.score(kind,'oc232-nodocker')['decode_tps']
    except Exception:cohort=None
    tps=statistics.median([r['decode_tps'] for r in measured if r['decode_tps']]) if any(r['decode_tps'] for r in measured) else None
    usable=bool(measured) and passes/len(measured)>=BAR_PASS and statistics.median(walls)<=BAR_MEDIAN_S
    return {'kind':kind,'file':str(path),'rows':rows,'passes':passes,'measured':len(measured),'of':len(rows),'truncated':sum(r['truncated'] for r in measured),
            'median_s':statistics.median(walls) if walls else None,'p90_s':p90(walls) if walls else None,
            'median_ttft_s':statistics.median([r['ttft_s'] for r in measured if r['ttft_s'] is not None]) if measured else None,
            'decode_tps':tps,'cohort_decode_tps':cohort,'slow_decode_flag':bool(tps and cohort and tps<.7*cohort),
            'memory_gate':gate.get(kind),'verdict':'N/E (memory gate)' if gate.get(kind) else 'usable' if usable else 'not usable'}

def main():
    if '--selfcheck' in sys.argv:return selfcheck()
    kinds=[a for a in sys.argv[1:] if not a.startswith('-')] or ['gguf','bonsai9']
    log=ROOT/'logs/memory-gate-oc232-chat.jsonl'
    gate=breaches([json.loads(l) for l in log.read_text().splitlines() if l.strip()]) if log.exists() else {}
    out=[summarize(k,sorted((ROOT/'benchmarks/results').glob(f'chat-{k}-2*.json'))[-1],gate) for k in kinds]
    p=ROOT/'benchmarks/results'/f"chat-graded-{datetime.datetime.now():%Y%m%dT%H%M%S}.json";p.write_text(json.dumps(out,indent=1)+'\n');print(p)
    tasks=[t['id'] for t in json.loads((CHAT/'tasks.json').read_text())['tasks']]
    print(f'Bar (D062): pass rate >= {BAR_PASS:.0%} of measured answers and median answer time <= {BAR_MEDIAN_S} s; memory-gate breach = N/E.')
    print('| Model | '+' | '.join(tasks)+' | Pass | Truncated | Median s | p90 s | TTFT s | Decode t/s (cohort) | Gate | Verdict |')
    print('|'+'---|'*(len(tasks)+10))
    for s in out:
        per=' | '.join(f"{sum(r['status']=='pass' for r in s['rows'] if r['task']==t)}/{sum(r['task']==t for r in s['rows'])}" for t in tasks)
        f=lambda v,d=0:'N/E' if v is None else f'{v:.{d}f}'
        print(f"| {s['kind']} | {per} | {s['passes']}/{s['measured']} | {s['truncated']} | {f(s['median_s'])} | {f(s['p90_s'])} | {f(s['median_ttft_s'])} | {f(s['decode_tps'],1)} ({f(s['cohort_decode_tps'],1)}){' SLOW' if s['slow_decode_flag'] else ''} | {s['memory_gate'] or 'clean'} | {s['verdict']} |")

if __name__=='__main__':main()
