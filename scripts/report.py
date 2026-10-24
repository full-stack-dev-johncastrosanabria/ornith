"""Derive a cautious report from saved measurements; absent is never zero."""
import csv,datetime,json,pathlib,re,statistics
ROOT=pathlib.Path(__file__).resolve().parents[1]
RESULTS=ROOT/'benchmarks/results'
def latest(pattern):
    files=sorted(RESULTS.glob(pattern));return json.loads(files[-1].read_text()) if files else None
def medrange(values,unit=''):
    v=[x for x in values if isinstance(x,(int,float))]
    return f'{statistics.median(v):.2f}{unit} ({min(v):.2f}–{max(v):.2f}, n={len(v)})' if v else 'N/E'
def group(kind,label):
    selected={}
    for path in sorted(RESULTS.glob(f'tasks-{kind}-{label}-*.json')):
        data=json.loads(path.read_text())
        for row in data.get('rows',[]):
            row['evidence_file']=path.name
            selected[row['task']]=row
    return [selected[k] for k in sorted(selected)]
def memory(rows):
    samples=[s for r in rows for s in r.get('agent',{}).get('memory_samples',[])]
    rss=[int(s['server_rss_kib'])/1024**2 for s in samples if s.get('server_rss_kib','').isdigit()]
    swap=[]
    for s in samples:
        m=re.search(r'used = ([\d.]+)M',s.get('swap',''))
        if m:swap.append(float(m[1])/1024)
    return (f'{max(rss):.2f} GiB peak RSS' if rss else 'N/E',f'{min(swap):.2f}–{max(swap):.2f} GiB system swap' if swap else 'N/E')
def quality(rows):
    scored=[r for r in rows if r['status'] in ['pass','fail']]
    infra=sum(r['status']=='infrastructure' for r in rows)
    return (f"{sum(r['status']=='pass' for r in scored)}/{len(scored)} scored"+(f'; {infra} infrastructure' if infra else '')) if rows else 'N/E'
def tasktime(rows):
    times=[r['agent']['wall_s'] for r in rows if 'agent' in r and r['status']=='pass']
    return f'{statistics.median(times):.1f} s median, {len(times)} completed tasks' if times else 'N/E'
def execution_stats(row):
    events=row.get('agent',{}).get('events',[]);test_runs=0;test_retries=0;previous_failed=False;failed_commands=0
    for e in events:
        part=e.get('part',{});state=part.get('state',{})
        if e.get('type')!='tool_use' or part.get('tool')!='bash':continue
        code=state.get('metadata',{}).get('exit');failed_commands+=code is not None and code!=0
        command=state.get('input',{}).get('command','')
        if re.search(r'\bpytest\b|\bdotnet\s+test\b',command):
            test_runs+=1;test_retries+=previous_failed;previous_failed=code is not None and code!=0
    finishes=[e.get('part',{}).get('tokens',{}) for e in events if e.get('type')=='step_finish']
    reasons=[e.get('part',{}).get('reason') for e in events if e.get('type')=='step_finish']
    return {'tool_calls':row.get('tool_count'),'failed_shell_calls':failed_commands,'test_bearing_shell_calls':test_runs,'test_reruns_after_failure':test_retries,'provider_retries':None,'provider_retry_note':'not exposed by installed CLI JSON; do not equate zero error events with zero retries','error_events':sum(e.get('type')=='error' for e in events),'finish_reasons':reasons,'output_limit_events':reasons.count('length'),'first_tool_from_launch_s':row.get('first_tool_from_launch_s'),'tokens_input_uncached':sum(t.get('input',0) for t in finishes),'tokens_cache_read':sum(t.get('cache',{}).get('read',0) for t in finishes),'tokens_output_reported':sum(t.get('output',0) for t in finishes),'tokens_reasoning_reported':sum(t.get('reasoning',0) for t in finishes)}
def main():
    b=latest('micro-bonsai-*.json');m=latest('micro-mlx-direct-*.json');ma=latest('micro-mlx-20*.json');smoke=latest('smoke-agent-mlx-*.json');opt=latest('harness-local-*.json')
    br=group('bonsai','control');mr=group('mlx','control');hr=group('mlx','optimized')
    decodeb=medrange([r.get('timings',{}).get('predicted_per_second') for r in b['rows']]) if b else 'N/E'
    prefillb=medrange([r.get('timings',{}).get('prompt_per_second') for r in b['rows']]) if b else 'N/E'
    decodem=medrange([r.get('decode_tps') for r in m['rows']]) if m else 'N/E'
    prefillm=medrange([r.get('prefill_tps') for r in m['rows']]) if m else 'N/E'
    lines=['# Measured results', '',f"Generated {datetime.datetime.now(datetime.timezone.utc).isoformat()} from versioned JSON evidence.",'','**Exploratory comparison.** Short benchmarks have three repetitions; each F7/configuration is a single run. These are new public equivalents, not historical F7. No conclusive superiority claim from one task run.','', '| Indicator | Bonsai GGUF | Ornith MLX | Ornith GGUF | Ornith + local PPC |','|---|---|---|---|---|',f'| Decode t/s | {decodeb} | {decodem} | N/E | same runtime; no separate micro |',f'| Prefill t/s | {prefillb} | {prefillm} | N/E | same runtime; no separate micro |',f'| Peak measured server RSS | {memory(br)[0]} | {memory(mr)[0]} | N/E | {memory(hr)[0]} |',f"| Tool cycles | read cycle verified | {smoke.get('passed',0) if smoke else 'N/E'}/3 | N/E | see F7 tool events |",f'| F7 tasks | {quality(br)} | {quality(mr)} | N/E | {quality(hr)} |',f'| Agent wall/task | {tasktime(br)} | {tasktime(mr)} | N/E | {tasktime(hr)} |',f'| System swap during tasks | {memory(br)[1]} | {memory(mr)[1]} | N/E | {memory(hr)[1]} |','', 'Rates in the first two rows use native runtime counters: Bonsai HTTP timing fields, MLX direct stream_generate counters (different measurement paths, both fresh KV; not equivalent HTTP latency). For a runtime-only comparison use Ornith GGUF vs Ornith MLX with the same weights family/quantization quality; that comparison remains unexecuted. Do not infer pure runtime effects from Bonsai vs Ornith.','']
    if ma:
        lines+=['MLX HTTP transport measurements: TTFT '+medrange([r['ttft_s'] for r in ma['rows']],' s')+'; wall '+medrange([r['wall_s'] for r in ma['rows']],' s')+'. True prefill rate is not estimated from TTFT.','']
    lines+=['## Artifact acceptance versus agent completion','']
    for label,rows in [('Bonsai control',br),('Ornith control',mr),('Ornith local PPC',hr)]:
        if rows:
            accepted=sum(r.get('acceptance',{}).get('rc')==0 and r.get('tests_unchanged',False) for r in rows)
            completed=sum(r['status']=='pass' for r in rows)
            lines.append(f'- {label}: {accepted}/{len(rows)} artifacts pass external tests; {completed}/{len(rows)} agent runs completed successfully.')
    lines+=['','For example, the recorded Ornith F7-B artifact passes all three tests, but its agent run timed out at1200 seconds. This is a productivity/completion failure, not a claim that its final code fails those tests.','']
    lines+=['## External acceptance by task','','| Configuration | Task | Outcome | Agent seconds | Tool calls | Tool errors | Tests immutable |','|---|---|---|---|---|---|---|']
    flattened=[];observability=[]
    for label,rows in [('Bonsai control',br),('Ornith control',mr),('Ornith local PPC',hr)]:
        for row in rows:
            observability.append({'configuration':label,'task':row['task'],**execution_stats(row)})
            wall=row.get('agent',{}).get('wall_s');flat={'configuration':label,'task':row['task'],'outcome':row['status'],'wall_s':wall,'tool_calls':row.get('tool_count'),'tool_errors':row.get('tool_errors'),'tests_unchanged':row.get('tests_unchanged')};flattened.append(flat)
            lines.append(f"| {label} | {row['task']} | {row['status']} | {wall:.2f} | {row.get('tool_count','N/E')} | {row.get('tool_errors','N/E')} | {row.get('tests_unchanged','N/E')} |" if wall is not None else f"| {label} | {row['task']} | {row['status']} | N/E | N/E | N/E | N/E |")
    lines+=['','Failed acceptance, timeouts and infrastructure errors are retained. Passing artifact tests after an agent timeout is reported separately in raw JSON; it is not an end-to-end successful run. Tool errors count error events; they are not automatically equivalent to model retries. Context compaction and auxiliary requests are represented by raw event traces and server logs.','']
    for title,control,treatment in [('Bonsai to Ornith',br,mr),('Harness effect',mr,hr)]:
        pairs=[(x,next((y for y in treatment if y['task']==x['task']),None)) for x in control]
        pairs=[(x,y) for x,y in pairs if y and x['status']==y['status']=='pass']
        if pairs:
            lines+=[f'## {title} — paired passing tasks','']
            for x,y in pairs:
                reduction=100*(1-y['agent']['wall_s']/x['agent']['wall_s']);lines.append(f"- {x['task']}: {reduction:.1f}% agent-wall reduction ({x['agent']['wall_s']:.1f} → {y['agent']['wall_s']:.1f} s), one run per condition.")
            lines+=['']
    lines+=['## Harness cost and provenance','', 'Official unmodified Harness² deterministic demo: k1 sequential, 2/2 tasks, 8 Python executions, 8 deterministic editor calls. It does not measure Ornith. Official model-backed benchmark suites were not executed. WorkBuddy requires Docker and is excluded; local model-backed upstream source/Bun integration remains unvalidated.','']
    if opt:
        lines+=[f"Local Propose–Probe–Compose reproduction: k1, sequential, one worker, same Ornith MLX solver/improver/composer, DEV only. Optimization wall: {opt.get('optimization_wall_s','in progress')} seconds. That cost is separate from every final task wall. Composition is frozen before F7 optimized runs; F7 prompts, acceptance scores and solutions were not provided to the editor.",'']
    lines+=['## Not executed and limits','','- Ornith GGUF Q4_K_M: download would leave less than 8 GiB free; neither runtime build nor inference performed. Candidate startup/config files are not validation.','- Official model-backed Harness² benchmark adapters: not executed. The local reproduction is explicitly distinct.','- Three independent repetitions per long F7 task/configuration, seed blocks, thermal crossover and long-session soak: not executed.','- Production code review and security assessment: not scored by these bounded acceptance tests.','- A causal no-swapping claim: not established from system swap alone; inspect sampled swapin/swapout deltas and unrelated system activity. Initial system swap was already 1.23 GiB.','', '## Recommendation','', 'Prioritize externally correct completed tasks. Preserve Bonsai as the reference. Ornith MLX is usable only to the extent shown by measured tool and task outcomes above; no GGUF preference or conclusive overall model/harness advantage is established without the missing controlled repetitions.','']
    text='\n'.join(lines)
    (ROOT/'benchmarks/reports/observability.json').write_text(json.dumps(observability,indent=2)+'\n')
    (ROOT/'docs/RESULTS.md').write_text(text);(ROOT/'benchmarks/reports/comparison.md').write_text(text)
    with (ROOT/'benchmarks/reports/tasks.csv').open('w') as f:
        fields=['configuration','task','outcome','wall_s','tool_calls','tool_errors','tests_unchanged'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(flattened)
    print(ROOT/'docs/RESULTS.md')
if __name__=='__main__':main()
