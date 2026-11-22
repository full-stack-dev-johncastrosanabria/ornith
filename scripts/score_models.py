"""D031 model ranking from saved evidence only; no inference. Absent is N/E, never zero.

Rank: (1) end-to-end passes over the label's task set, quality first; (2) total agent time; (3) decode t/s.
D061: oc232 cohorts use F7+F8 (12 tasks), reported per set and combined; earlier labels keep F7 only.
If the top two differ by <=1 pass the verdict is provisional until a repeat cohort of both.
Best practices are descriptive only (passed tasks, violations introduced vs the fixture).
"""
import argparse,difflib,json,pathlib,re,sqlite3,statistics,subprocess
from report import RESULTS,ROOT,group,memory
from server import MLX_MODELS,load_profile
from memory_gate import breaches

KINDS=['mlx','bonsai','gguf','qwen','bonsai9','granite','gemma','sera8','gptoss']
NAMES={'mlx':'Ornith 1.5 9B MLX 4-bit','gguf':'Ornith 1.5 9B GGUF Q4_K_M','qwen':'Qwen3.5-9B MLX 4-bit',
       'bonsai9':'Ternary-Bonsai-2-9B PTQ1_0','granite':'Granite 4.1 8B MLX 4-bit','bonsai':'Bonsai 2 27B PTQ1_0',
       'gemma':'Gemma 4 12B MLX 4-bit','sera8':'SERA-8B GGUF Q4_K_M','gptoss':'GPT-OSS 20B MLX MXFP4-Q8'}
PROFILE=load_profile();CAP=PROFILE['output'];TIMEOUT=1200
SKIP={'tests','bin','obj','__pycache__','.pytest_cache','.ruff_cache','output'}
RUFF=str(ROOT/'runtimes/score/.venv/bin/ruff')
F7=['F7-A','F7-B','F7-C','F7-D'];F8=[f'F8-{c}' for c in 'ABCDEFGH']
# D061 amendment (user): long-context passes break ties before time.
LONG=['F8-A','F8-B','F8-C']
# D061 (d): fixed repeat sample when the top two differ by <=1 pass (label <label>-r2).
R2=['F8-A','F8-B','F8-C','F8-D','F8-E','F8-F']
# D061 (n): the pre-registered memory gate makes a breaching model infrastructure N/E; labels map to their gate log.
GATE_LOGS={'oc232-nodocker':'oc232'}
# User decision 2026-11-21 after seeing the data (labelled post-hoc deviation): Ornith GGUF's first-hour breach is waived.
GATE_WAIVED={('oc232-nodocker','gguf')}

def gate(kind,label):
    log=ROOT/f'logs/memory-gate-{GATE_LOGS[label]}.jsonl' if label in GATE_LOGS else None
    return breaches([json.loads(l) for l in log.read_text().splitlines() if l.strip()]).get(kind) if log and log.exists() else None

def repeat_passes(kind,label,tasks):
    """Passes on a pre-chosen repeat sample; None (N/E) until every task is pass/fail."""
    rows={r['task']:r for r in group(kind,label) if r['task'] in tasks}
    return sum(r['status']=='pass' for r in rows.values()) if len(rows)==len(tasks) and all(r['status'] in ('pass','fail') for r in rows.values()) else None

def task_set(label):
    return F7+F8 if label.startswith('oc232') else F7

def protocol(label):
    """D061 (user decision after the F8 pilot): oc232 cohorts run 40 agent steps and an 1800 s task timeout; earlier labels 12 / 1200."""
    return {'steps':40,'timeout':1800} if label.startswith('oc232') else {'steps':12,'timeout':TIMEOUT}

def cause(row):
    if row['status']=='pass':return '-'
    if row['status']!='fail':return 'infrastructure'
    if row['agent'].get('timeout'):return 'timeout'
    if not row.get('tests_unchanged',True):return 'tests_modified'
    if row.get('context_overflow'):return 'context_overflow'
    if compaction_failed(row):return 'compaction_failed'
    if dropped_calls(row):return 'dropped_tool_call'
    return 'incorrect (output cap hit)' if length_steps(row) else 'incorrect'

def steps(row):
    return sum(e.get('type')=='step_finish' for e in row['agent'].get('events',[]))

def dropped_calls(row):
    """Steps that ended with finish reason tool-calls but delivered no tool event: the runtime dropped the call
    (GPT-OSS DEV, 2026-11-20); OpenCode then sees an empty turn and ends the session as finished."""
    n=dropped=0
    for e in row['agent'].get('events',[]):
        if e.get('type')=='step_start':n=0
        elif e.get('type')=='tool_use':n+=1
        elif e.get('type')=='step_finish' and e.get('part',{}).get('reason')=='tool-calls' and not n:dropped+=1
    return dropped

def compaction_failed(row):
    """D061 pilot 2: OpenCode ends the session when its compaction summary outgrows its token budget."""
    return any(e.get('type')=='error' and e.get('error',{}).get('type')=='compaction.failed' for e in row['agent'].get('events',[]))

def compactions(row):
    """Completed/failed compactions from the run's own OpenCode database; N/E if it is missing."""
    db=pathlib.Path(row['agent'].get('state',''))/'data/opencode/opencode.db'
    if not db.is_file():return None
    with sqlite3.connect(f'file:{db}?mode=ro',uri=True) as c:
        data=[json.loads(d) for (d,) in c.execute("select data from session_message where type='compaction'")]
    return {'completed':sum(d.get('status')=='completed' for d in data),'failed':sum(d.get('status')=='failed' for d in data)}

def peak_input(row):
    """Largest prompt of any single model call (fresh input plus cache read)."""
    return max([t.get('input',0)+t.get('cache',{}).get('read',0) for e in row['agent'].get('events',[]) if e.get('type')=='step_finish' for t in [e.get('part',{}).get('tokens') or {}]] or [0]) or None

def end(row,budget):
    """How the agent session ended (D061): timeout, context_overflow, compaction_failed, step_cap or done."""
    if row['agent'].get('timeout'):return 'timeout'
    if row.get('context_overflow'):return 'context_overflow'
    if compaction_failed(row):return 'compaction_failed'
    if dropped_calls(row):return 'dropped_tool_call'
    return 'step_cap' if steps(row)>=budget else 'done'

def gross(row):
    """D061 DEV filter (user): gross agent failures only; the DEV pass itself is recorded, never selected on (n=1)."""
    ev=row['agent'].get('events',[]);tools=[e.get('part',{}) for e in ev if e.get('type')=='tool_use']
    calls=[(t.get('tool'),json.dumps(t.get('state',{}).get('input'),sort_keys=True)) for t in tools]
    text=' '.join(e.get('part',{}).get('text','') for e in ev if e.get('type')=='text')
    found=[];empty=dropped_calls(row)
    # Tool-call markup left in plain text means the runtime did not parse it into an action (Harmony / qwen XML).
    if empty or not any(t.get('state',{}).get('status')=='completed' for t in tools) or re.search(r'<tool_call>|<function=|<\|channel\|>|to=functions\.',text):found.append('tool calls not executed')
    if any(calls[i]==calls[i+1]==calls[i+2] for i in range(len(calls)-2)):found.append('loop (3 identical consecutive tool calls)')
    if length_steps(row):found.append('output cap hit')
    if compaction_failed(row) or row.get('context_overflow'):found.append(end(row,protocol(row.get('label',''))['steps']))
    return found

def length_steps(row):
    return sum(e.get('part',{}).get('reason')=='length' or e.get('part',{}).get('tokens',{}).get('output',0)>=CAP
               for e in row['agent']['events'] if e.get('type')=='step_finish')

def files(root):
    return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file() and not SKIP & set(p.relative_to(root).parts[:-1]) and p.suffix!='.pyc'}

def lint_count(paths,cwd):
    py=[str(p) for p in paths if p.suffix=='.py']
    if not py:return 0
    out=subprocess.run([RUFF,'check','--no-cache','--output-format','json','--isolated',*py],cwd=cwd,capture_output=True,text=True).stdout
    fmt=subprocess.run([RUFF,'format','--no-cache','--isolated','--check',*py],cwd=cwd,capture_output=True,text=True).stdout
    return len(json.loads(out or '[]'))+fmt.count('Would reformat')

def dotnet_dirty(root):
    src=root/'src'
    if not src.exists():return 0
    p=subprocess.run(['dotnet','format','whitespace',str(src),'--folder','--verify-no-changes'],capture_output=True,text=True)
    return int(p.returncode!=0)

def practices(row):
    work=pathlib.Path(row['workspace']);fixture=ROOT/'benchmarks/fixtures'/row['task']
    if not work.exists():return {'status':'N/E: workspace missing'}
    a,b=files(fixture),files(work)
    changed=[k for k in b if k in a and a[k].read_bytes()!=b[k].read_bytes()];added=[k for k in b if k not in a]
    plus=minus=0
    for k in changed:
        for line in difflib.unified_diff(a[k].read_text(errors='replace').splitlines(),b[k].read_text(errors='replace').splitlines(),lineterm=''):
            if line.startswith('+') and not line.startswith('+++'):plus+=1
            elif line.startswith('-') and not line.startswith('---'):minus+=1
    touched=changed+added
    lint=lint_count([b[k] for k in touched],work)-lint_count([a[k] for k in changed],fixture)
    return {'files_changed':len(changed),'files_added':added,'lines_added':plus,'lines_removed':minus,
            'lint_introduced':lint,'dotnet_format_introduced':dotnet_dirty(work)-dotnet_dirty(fixture) if (fixture/'tests/Acceptance.csproj').exists() else None,
            'tests_unchanged':row.get('tests_unchanged')}

def decode(kind,label):
    if kind in MLX_MODELS:
        rows=[json.loads(p.read_text()) for p in sorted(RESULTS.glob(f'micro-{kind}-direct-*.json'))]
        rows=[d for d in rows if d.get('kind')==kind]
        return rows[-1]['medians']['decode_tps'] if rows else None
    rows=[json.loads(p.read_text()) for p in sorted(RESULTS.glob(f'micro-{kind}-20*.json'))]
    rows=[d for d in rows if d.get('label')==label]
    v=[r['timings'].get('predicted_per_second') for r in rows[-1]['rows'] if r.get('timings')] if rows else []
    return statistics.median(v) if v else None

def footprint_gib(rows):
    """Peak physical footprint (top MEM) of the server; RSS undercounts Metal allocations."""
    units={'B':1/1024**3,'K':1/1024**2,'M':1/1024,'G':1.0}
    v=[float(m[1])*units[m[2]] for r in rows for s in r['agent'].get('memory_samples',[]) for line in s.get('server_footprint',[])
       for m in [re.match(r'\s*([\d.]+)([BKMG])',line)] if m]
    return f'{max(v):.2f} GiB' if v else 'N/E'

def score(kind,label):
    expected=task_set(label);rows=[r for r in group(kind,label) if r['task'] in expected]
    complete=sorted(r['task'] for r in rows)==sorted(expected) and all(r['status'] in ('pass','fail') for r in rows)
    budget=protocol(label)['steps']
    tasks=[{'task':r['task'],'status':r['status'],'cause':cause(r),'wall_s':r['agent']['wall_s'],'steps':steps(r),'headroom':1-r['agent']['wall_s']/protocol(label)['timeout'],
            'cap_hits':length_steps(r),'end':end(r,budget),'peak_input':peak_input(r),'compactions':compactions(r),'tools':r.get('tool_count'),'practices':practices(r) if r['status']=='pass' else None,'evidence':r['evidence_file']} for r in rows]
    rss,swap=memory(rows)
    passes=lambda p:sum(t['status']=='pass' for t in tasks if t['task'].startswith(p)) if complete else None
    breach=gate(kind,label)
    return {'kind':kind,'model':NAMES[kind],'complete':complete,'memory_gate':breach,'gate_waived':bool(breach) and (label,kind) in GATE_WAIVED,'n':len(rows),'of':len(expected),'passes':passes('F'),'passes_f7':passes('F7'),
            'passes_f8':passes('F8') if len(expected)>len(F7) else None,
            'passes_long':sum(t['status']=='pass' for t in tasks if t['task'] in LONG) if complete else None,
            # D061 amendment: a timeout before the step budget means speed, not only quality, decided that task.
            'timeouts':[f"{t['task']}@{t['steps']}/{budget}" for t in tasks if t['cause']=='timeout'],
            'timeouts_before_budget':sum(t['cause']=='timeout' and t['steps']<budget for t in tasks),
            'total_s':sum(t['wall_s'] for t in tasks) if complete else None,
            'peak_input':max([t['peak_input'] or 0 for t in tasks] or [0]) or None,
            'compactions':{k:sum((t['compactions'] or {}).get(k,0) for t in tasks) for k in ('completed','failed')} if all(t['compactions'] for t in tasks) else None,'decode_tps':decode(kind,label),'peak_footprint':footprint_gib(rows),'peak_rss':rss,'swap':swap,'tasks':tasks}

def shared_speed(a,b):
    """User amendment: compare speed only on tasks both models passed."""
    won=lambda s:{t['task']:t['wall_s'] for t in s['tasks'] if t['status']=='pass'}
    both=sorted(set(won(a))&set(won(b)))
    return {'tasks':both,a['kind']:sum(won(a)[t] for t in both),b['kind']:sum(won(b)[t] for t in both)}

def rank(scores):
    ranked=sorted([s for s in scores if s['complete'] and (not s.get('memory_gate') or s.get('gate_waived'))],key=lambda s:(-s['passes'],-(s.get('passes_long') or 0),s['total_s'],-(s['decode_tps'] or 0)))
    provisional=len(ranked)>1 and ranked[0]['passes']-ranked[1]['passes']<=1
    return ranked,provisional

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--label',default='oc226-nodocker');ap.add_argument('--kinds',nargs='+',default=KINDS);ap.add_argument('--dev-filter',action='store_true');a=ap.parse_args()
    if a.dev_filter:
        for k in a.kinds:
            rows=[r for r in group(k,a.label) if r['task']=='DEV']
            print(k,'N/E: not run' if not rows else f"DEV {rows[-1]['status']} (recorded only); filter: {', '.join(gross(rows[-1])) or 'ok'}")
        return
    scores=[score(k,a.label) for k in a.kinds];ranked,provisional=rank(scores)
    shared=shared_speed(*ranked[:2]) if len(ranked)>1 else None
    out={'rule':'D031','label':a.label,'ranking':[s['kind'] for s in ranked],'provisional':provisional,'shared_pass_speed':shared,'scores':scores}
    (ROOT/'benchmarks/reports'/f'model-selection-{a.label}.json').write_text(json.dumps(out,indent=2)+'\n')
    lines=[f'Ranking under the fixed profile ({a.label}; {PROFILE["context"]//1024}K/{CAP} incl. reasoning/.6/.95, Bonsai reasoning-budget 100, others unbounded) — not model capability with unlimited reasoning.','',f'| # | Model | F7 pass | F8 pass | Total pass | Long (F8 A–C) | Total s | Decode t/s | Peak footprint | Timeouts (step reached) | Fail causes |','|---|---|---|---|---|---|---|---|---|---|---|']
    for i,s in enumerate(ranked+[s for s in scores if s not in ranked],1):
        causes=', '.join(f"{t['task']}:{t['cause']}" for t in s['tasks'] if t['status']!='pass') or '-'
        f8=f"{s['passes_f8']}/{len(F8)}" if s['passes_f8'] is not None else '-'
        long=f"{s['passes_long']}/{len(LONG)}" if s['passes_f8'] is not None else '-'
        seen=sum(t['status']=='pass' for t in s['tasks'])
        head=(f"| {i} | {s['model']} | {s['passes_f7']}/{len(F7)} | {f8} | {s['passes']}/{s['of']} | {long} | {s['total_s']:.0f} | " if s in ranked
              else f"| N/E | {s['model']} | N/E | N/E | N/E (memory gate: {s['memory_gate']}; {seen} pass in {s['n']}/{s['of']}, descriptive) | N/E | N/E | " if s['memory_gate']
              else f"| N/E | {s['model']} | N/E | N/E | N/E ({s['n']}/{s['of']} scored) | N/E | N/E | ")
        lines.append(head+(f"{s['decode_tps']:.2f}" if s['decode_tps'] else 'N/E')+f" | {s['peak_footprint']} | {', '.join(s['timeouts']) or '-'} | {causes} |")
    lines+=['','| Model | Peak input tokens/call | Compactions ok/failed | Swap | Session end |','|---|---|---|---|---|']
    for s in scores:
        c=s.get('compactions');ends={}
        for t in s['tasks']:ends[t['end']]=ends.get(t['end'],0)+1
        ok_failed=f"{c['completed']}/{c['failed']}" if c else 'N/E';ended=', '.join(f'{k} {v}' for k,v in sorted(ends.items())) or 'N/E'
        lines.append(f"| {s['model']} | {s.get('peak_input') or 'N/E'} | {ok_failed} | {s['swap']} | {ended} |")
    lines+=[f"\nMemory gate waived by user decision after seeing the data (post-hoc deviation, D061 (n)): {s['model']} ({s['memory_gate']})." for s in scores if s['gate_waived']]
    if shared and shared['tasks']:lines.append(f"\nSpeed on the {len(shared['tasks'])} tasks both top models passed: "+', '.join(f"{NAMES[k]} {v:.0f} s" for k,v in shared.items() if k!='tasks'))
    if provisional:
        lines.append('\nProvisional: the top two differ by <=1 pass; D031 requires a repeat cohort of both before a final verdict.')
        if a.label.startswith('oc232'):
            r2={s['kind']:repeat_passes(s['kind'],a.label+'-r2',R2) for s in ranked[:2]};out['repeat_r2']=r2
            lines.append('Repeat '+', '.join(f"{NAMES[k]} {'N/E' if v is None else f'{v}/{len(R2)}'}" for k,v in r2.items())+f' on {"/".join(R2)} (label {a.label}-r2); verdict on all 18 runs.')
            (ROOT/'benchmarks/reports'/f'model-selection-{a.label}.json').write_text(json.dumps(out,indent=2)+'\n')
    print('\n'.join(lines))

if __name__=='__main__':main()
