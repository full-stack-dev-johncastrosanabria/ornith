"""D040/D041 cloud-assisted optimization arms, local inference (Ornith MLX). Never reported as official or local-only Harness².

Arms, each written by a fresh Claude Code subagent (model opus):
  editor   Harness² INV mission + attempt-1 DEV editor workspace, delivered by exactly one Read of editor/input.md
  control  blind: generic work description + base harness + target length; no DEV, rollouts, results or F7; zero tools
Commands:
  bundle ARM             write the verbatim input (control needs the editor's frozen guidance for its length)
  ingest ARM TRANSCRIPT  audit the copied transcript, apply edits, DEV-string scan, freeze guidance
  evaluate               smoke gate, DEV once per arm (recorded only), F7 A-D interleaved across arms, comparison
"""
import argparse,hashlib,json,os,pathlib,re,shutil,subprocess
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
RUN=ROOT/'harness2/official/runs/20261108T134833'
CTX=RUN/'runs/f7-native-local-oc-seq1/DEV/context/inv1'
OUT=ROOT/'harness2/official/cloud-editor'
ALWAYS_ON=('systemprompt.md','guardrails.md','LongTermMEMORY.md','tool_descriptions/tool_guidance.md')
# D041 pre-registered DEV-specific strings: identifiers, file names and literal test values of the DEV fixture.
REJECT=[r'normalize\s*\(',r'normalize\.py',r'test_normalize',r"' B '",r"\[\s*'a'\s*,\s*'b'\s*\]"]
NONE='official-source-control-c20261108'
LABELS={'editor':'cloud-editor-treatment-c20261108','control':'blind-control-c20261108'}
# D041 balanced order against thermal and time drift on a fanless Air.
ORDER=[('F7-A','editor'),('F7-A','control'),('F7-B','control'),('F7-B','editor'),('F7-C','editor'),('F7-C','control'),('F7-D','control'),('F7-D','editor')]
TOLERANCE=.25
EDITOR_HEADER='''You are the Harness² editor for one run. After reading this file, do not call any other tool and do not ask questions. Everything you would read is reproduced verbatim below, each file between a <<<WORKSPACE FILE path>>> line and an <<<END>>> line: MISSION.md (your instructions) and the editor workspace under context/.

Adapter (it replaces file operations only; follow MISSION.md for everything else):
- Read the copies below; you cannot run commands, tests or scripts.
- To edit a file under context/harness/, output its complete new content:
<<<EDIT context/harness/RELATIVE_PATH>>>
complete new file content
<<<END EDIT>>>
- Files you do not output stay byte-identical. Only the four always-on files may be edited: context/harness/systemprompt.md, context/harness/guardrails.md, context/harness/LongTermMEMORY.md, context/harness/tool_descriptions/tool_guidance.md.
- Instead of saving output/answer.md, output the requested final response once:
<<<ANSWER>>>
final response
<<<END ANSWER>>>
- Output nothing outside these blocks.'''
CONTROL_TEMPLATE='''You are writing the always-on guidance of an autonomous coding agent's harness. Do not call any tool and do not ask questions.

The agent's work: make small correct programming changes and verify them locally. It runs in OpenCode (file read, edit and shell tools) on a small local model. You have no example runs, tasks, rollouts or results: write generally useful guidance for this work.

The harness has four always-on files, injected into every run. Their current contents follow, each between a <<<FILE path>>> line and an <<<END>>> line.

{files}

Length: together the four files must total about {n} characters (between {lo} and {hi}).

To edit a file, output its complete new content:
<<<EDIT context/harness/RELATIVE_PATH>>>
complete new file content
<<<END EDIT>>>
Files you do not output stay unchanged. Only these four files may be edited. Then give a short rationale once:
<<<ANSWER>>>
rationale
<<<END ANSWER>>>
Output nothing outside these blocks.'''
EDIT=re.compile(r'^<<<EDIT context/harness/(\S+)>>>\n(.*?)\n?^<<<END EDIT>>>$',re.S|re.M)
ANSWER=re.compile(r'^<<<ANSWER>>>\n(.*?)\n?^<<<END ANSWER>>>$',re.S|re.M)

def sha(text):return hashlib.sha256(text.encode()).hexdigest()

def bundle(arm):
    d=OUT/arm;d.mkdir(parents=True,exist_ok=True)
    if arm=='editor':
        mission=next((RUN/'editor').glob('inv1.a1.*.mission.md'))
        files=[('MISSION.md',mission)]+[(f'context/{p.relative_to(CTX)}',p) for p in sorted(CTX.rglob('*')) if p.is_file()]
        text='\n\n'.join([EDITOR_HEADER]+[f'<<<WORKSPACE FILE {name}>>>\n{p.read_text()}\n<<<END>>>' for name,p in files])+'\n'
        prompt=f'Use the Read tool exactly once to read the whole file {d/"input.md"} (no offset or limit), then follow the instructions in that file. Do not call any other tool.'
    else:
        n=len((OUT/'editor/frozen-guidance.txt').read_text())  # D041: length-matched to the editor guidance
        files='\n\n'.join(f'<<<FILE context/harness/{rel}>>>\n{(CTX/"harness"/rel).read_text()}<<<END>>>' for rel in ALWAYS_ON)
        text=prompt=CONTROL_TEMPLATE.format(files=files,n=n,lo=round(n*(1-TOLERANCE)),hi=round(n*(1+TOLERANCE)))
    (d/'input.md').write_text(text);(d/'prompt.txt').write_text(prompt)
    meta={'arm':arm,'input_sha256':sha(text),'prompt_sha256':sha(prompt),'input_chars':len(text)}
    (d/'input.json').write_text(json.dumps(meta,indent=2)+'\n');print(d/'prompt.txt',meta)

def parse(text):
    edits={m[1]:m[2] for m in EDIT.finditer(text)}
    return edits,ANSWER.findall(text),ANSWER.sub('',EDIT.sub('',text)).strip(),[p for p in edits if p not in ALWAYS_ON]

def scan(text):
    return {p:len(re.findall(p,text)) for p in REJECT if re.search(p,text)},len(re.findall(r'\bnormalize\b',text,re.I))

def blocks(m):
    c=m.get('content');return [{'type':'text','text':c}] if isinstance(c,str) else c or []

def text_of(b):
    c=b.get('content');return c if isinstance(c,str) else ''.join(x.get('text','') for x in c or [] if isinstance(x,dict))

def ingest(arm,transcript):
    import harness_official as h
    d=OUT/arm
    for name in ('harness','frozen-guidance.txt','audit.json','answer.md','output.md','transcript.jsonl'):
        p=d/name;shutil.rmtree(p) if p.is_dir() else p.unlink(missing_ok=True)
    t=d/'transcript.jsonl';shutil.copy2(transcript,t)
    msgs=[o['message'] for o in map(json.loads,filter(str.strip,t.read_text().splitlines())) if isinstance(o.get('message'),dict)]
    asst=[m for m in msgs if m.get('role')=='assistant']
    uses=[b for m in asst for b in blocks(m) if b.get('type')=='tool_use']
    results=[b for m in msgs if m.get('role')=='user' for b in blocks(m) if b.get('type')=='tool_result']
    expected=(d/'input.md').read_text().strip()
    if arm=='editor':
        args=uses[0].get('input',{}) if uses else {}
        permitted=len(uses)==1 and uses[0].get('name')=='Read' and args.get('file_path')==str(d/'input.md') and not {'offset','limit'}&set(args)
        # Read returns cat -n lines (number, tab, content) plus harness reminders; strip the numbers and require containment.
        seen='\n'.join(re.sub(r'^\s*\d+\t','',line,count=1) for line in text_of(results[0]).splitlines()) if results else ''
    else:
        permitted=not uses
        seen=next((''.join(b.get('text','') for b in blocks(m) if b.get('type')=='text') for m in msgs if m.get('role')=='user'),'')
    final='\n'.join(b['text'] for m in asst for b in blocks(m) if b.get('type')=='text');(d/'output.md').write_text(final)
    edits,answers,outside,bad=parse(final)
    cand=d/'harness';shutil.copytree(CTX/'harness',cand)
    for rel,content in edits.items():
        if rel in ALWAYS_ON:(cand/rel).write_text(content+'\n' if content else '')
    if answers:(d/'answer.md').write_text(answers[0]+'\n')
    guidance=h.text_harness(cand);hits,word=scan(guidance)  # official always-on composition and text-only validation
    target=len((OUT/'editor/frozen-guidance.txt').read_text()) if arm=='control' else None
    audit={'decision':'D041','arm':arm,'label':LABELS[arm],'models':sorted({m.get('model') for m in asst}-{None}),
           'tool_calls':[{'name':u.get('name'),'input':u.get('input')} for u in uses],'permitted_tools':permitted,'input_delivered_verbatim':expected in seen,
           'input_sha256':sha((d/'input.md').read_text()),'edited':sorted(edits),'outside_whitelist':bad,'answer_blocks':len(answers),
           'text_outside_blocks_chars':len(outside),'reject_hits':hits,'word_normalize_count':word,'guidance_chars':len(guidance),
           'guidance_sha256':sha(guidance),'target_chars':target}
    audit['status']=('infrastructure: unpermitted tool use' if not permitted else 'infrastructure: input not delivered verbatim' if not audit['input_delivered_verbatim']
                     else 'malformed output' if bad or len(answers)!=1 else 'contaminated: DEV-specific strings' if hits
                     else 'no change' if guidance==h.text_harness(CTX/'harness')
                     else 'length out of range' if target and abs(len(guidance)-target)>TOLERANCE*target else 'ok')
    if audit['status']=='ok':(d/'frozen-guidance.txt').write_text(guidance)
    (d/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({k:v for k,v in audit.items() if k!='tool_calls'},indent=2))

def evaluate():
    import bench_tasks,smoke_agent,harness_official as h
    from server import STATE,start,stop
    lock=ROOT/'logs/campaign.lock'
    if STATE.exists() or lock.exists():raise SystemExit('A server or campaign is active; refusing to share it')
    for arm in LABELS:
        if json.loads((OUT/arm/'audit.json').read_text())['status']!='ok':raise SystemExit(f'{arm} candidate not usable; see audit.json')
    guidance={arm:(OUT/arm/'frozen-guidance.txt').read_text() for arm in LABELS}
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        h.configure();start('mlx');s=json.loads(STATE.read_text())
        with patch.object(smoke_agent,'run',h.source_run):smoke_agent.main()
        for arm in LABELS:
            dev=OUT/arm/'dev-result.json'
            if not dev.exists():
                with patch.object(bench_tasks,'run',h.source_run):row=bench_tasks.task('DEV',s,guidance[arm],label=f'{arm}-dev',timeout=600)
                dev.write_text(json.dumps(row,indent=2)+'\n');print('DEV',arm,row['status'],flush=True)
        for tid,arm in ORDER:h.evaluate(LABELS[arm],guidance[arm],tasks=(tid,))
    finally:
        if STATE.exists():stop()
        lock.unlink(missing_ok=True)
    report()

def report():
    labels={'none':NONE,**LABELS}
    rows={k:[json.loads(p.read_text())['rows'][0] for p in sorted((ROOT/'benchmarks/results').glob(f'tasks-mlx-{l}-F7-*.json'))] for k,l in labels.items()}
    cond={k:{'label':labels[k],'complete':len(v)==4 and all(r['status'] in ('pass','fail') for r in v),'end_to_end':sum(r['status']=='pass' for r in v),
             'artifact':sum(bool(r.get('artifact_acceptance')) for r in v),'tasks':{r['task']:{'status':r['status'],'wall_s':round(r['agent']['wall_s'])} for r in v}} for k,v in rows.items()}
    def compare(a,b):
        if not (cond[a]['complete'] and cond[b]['complete']):return 'N/E: incomplete condition'
        d=cond[a]['end_to_end']-cond[b]['end_to_end'];return {'delta':d,'verdict':'better' if d>=2 else 'worse' if d<=-2 else 'no detectable difference at n=4'}
    out={'decision':'D041','classification':'cloud-assisted optimization (Claude writers), local inference (Ornith MLX, pinned OpenCode source executor)',
         'conditions':cond,'editor_vs_none':compare('editor','none'),'control_vs_none':compare('control','none'),'editor_vs_control':compare('editor','control'),
         'dev':{arm:json.loads((OUT/arm/'dev-result.json').read_text())['status'] for arm in LABELS},
         'guidance_chars':{arm:len((OUT/arm/'frozen-guidance.txt').read_text()) for arm in LABELS},'none_condition_not_interleaved':True}
    (ROOT/'benchmarks/reports/cloud-editor-comparison-c20261108.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['bundle','ingest','evaluate','report']);ap.add_argument('arm',nargs='?',choices=list(LABELS))
    ap.add_argument('transcript',nargs='?',type=pathlib.Path);a=ap.parse_args()
    if a.action=='bundle':bundle(a.arm)
    elif a.action=='ingest':ingest(a.arm,a.transcript)
    else:{'evaluate':evaluate,'report':report}[a.action]()
