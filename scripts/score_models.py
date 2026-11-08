"""D031 model ranking from saved evidence only; no inference. Absent is N/E, never zero.

Rank: (1) F7 end-to-end passes, quality first; (2) total F7 agent time; (3) decode t/s.
If the top two differ by <=1 pass the verdict is provisional until a repeat cohort of both.
Best practices are descriptive only (passed tasks, violations introduced vs the fixture).
"""
import argparse,difflib,json,pathlib,re,statistics,subprocess
from report import RESULTS,ROOT,group,memory

KINDS=['mlx','gguf','qwen','bonsai9','granite','bonsai']
NAMES={'mlx':'Ornith 1.5 9B MLX 4-bit','gguf':'Ornith 1.5 9B GGUF Q4_K_M','qwen':'Qwen3.5-9B MLX 4-bit',
       'bonsai9':'Ternary-Bonsai-2-9B PTQ1_0','granite':'Granite 4.1 8B MLX 4-bit','bonsai':'Bonsai 2 27B PTQ1_0'}
CAP=4096;TIMEOUT=1200
SKIP={'tests','bin','obj','__pycache__','.pytest_cache','.ruff_cache','output'}
RUFF=str(ROOT/'runtimes/score/.venv/bin/ruff')

def cause(row):
    if row['status']=='pass':return '-'
    if row['status']!='fail':return 'infrastructure'
    if row['agent'].get('timeout'):return 'timeout'
    if not row.get('tests_unchanged',True):return 'tests_modified'
    return 'incorrect (output cap hit)' if length_steps(row) else 'incorrect'

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
            'lint_introduced':lint,'dotnet_format_introduced':dotnet_dirty(work)-dotnet_dirty(fixture) if row['task']=='F7-A' else None,
            'tests_unchanged':row.get('tests_unchanged')}

def decode(kind,label):
    if kind in ('mlx','qwen','granite'):
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
    rows=group(kind,label)
    complete=len(rows)==4 and all(r['status'] in ('pass','fail') for r in rows)
    tasks=[{'task':r['task'],'status':r['status'],'cause':cause(r),'wall_s':r['agent']['wall_s'],'headroom':1-r['agent']['wall_s']/TIMEOUT,
            'cap_hits':length_steps(r),'tools':r.get('tool_count'),'practices':practices(r) if r['status']=='pass' else None,'evidence':r['evidence_file']} for r in rows]
    rss,swap=memory(rows)
    return {'kind':kind,'model':NAMES[kind],'complete':complete,'n':len(rows),'passes':sum(t['status']=='pass' for t in tasks) if complete else None,
            'total_s':sum(t['wall_s'] for t in tasks) if complete else None,'decode_tps':decode(kind,label),'peak_footprint':footprint_gib(rows),'peak_rss':rss,'swap':swap,'tasks':tasks}

def rank(scores):
    ranked=sorted([s for s in scores if s['complete']],key=lambda s:(-s['passes'],s['total_s'],-(s['decode_tps'] or 0)))
    provisional=len(ranked)>1 and ranked[0]['passes']-ranked[1]['passes']<=1
    return ranked,provisional

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--label',default='oc226-nodocker');ap.add_argument('--kinds',nargs='+',default=KINDS);a=ap.parse_args()
    scores=[score(k,a.label) for k in a.kinds];ranked,provisional=rank(scores)
    out={'rule':'D031','label':a.label,'ranking':[s['kind'] for s in ranked],'provisional':provisional,'scores':scores}
    (ROOT/'benchmarks/reports'/f'model-selection-{a.label}.json').write_text(json.dumps(out,indent=2)+'\n')
    lines=[f'| # | Model | F7 pass | Total s | Decode t/s | Peak footprint | Fail causes |','|---|---|---|---|---|---|---|']
    for i,s in enumerate(ranked+[s for s in scores if not s['complete']],1):
        causes=', '.join(f"{t['task']}:{t['cause']}" for t in s['tasks'] if t['status']!='pass') or '-'
        head=f"| {i} | {s['model']} | {s['passes']}/4 | {s['total_s']:.0f} | " if s['complete'] else f"| N/E | {s['model']} | N/E ({s['n']}/4 scored) | N/E | "
        lines.append(head+(f"{s['decode_tps']:.2f}" if s['decode_tps'] else 'N/E')+f" | {s['peak_footprint']} | {causes} |")
    if provisional:lines.append('\nProvisional: the top two differ by <=1 F7 pass; D031 requires a repeat cohort of both before a final verdict.')
    print('\n'.join(lines))

if __name__=='__main__':main()
