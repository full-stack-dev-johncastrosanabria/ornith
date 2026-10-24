"""Three actual OpenCode tool cycles with independent observable checks."""
import datetime,json,pathlib,shutil,uuid
from opencode_local import run
from bench_tasks import grade,hashes
ROOT=pathlib.Path(__file__).resolve().parents[1]

def main():
    s=json.loads((ROOT/'logs/server.json').read_text());rows=[]
    dest=ROOT/'benchmarks/results'/f"smoke-agent-{s['kind']}-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    py=str(ROOT/'benchmarks/.venv/bin/python')
    for cycle in ['read','edit_test','debug']:
        work=ROOT/'benchmarks/work'/f"smoke-{s['kind']}-{cycle}-{uuid.uuid4().hex[:8]}";work.mkdir(parents=True)
        if cycle=='read':
            (work/'README.md').write_text('Verification marker: NATIVE-M3-4829\n')
            prompt='Read README.md with a file tool and return its verification marker exactly.'
        else:
            (work/'tests').mkdir();(work/'tests/test_math.py').write_text('from math_ops import increment\ndef test_increment():\n    assert increment(3)==4\n    assert increment(-1)==0\n')
            (work/'math_ops.py').write_text('def increment(n):\n    '+('raise NotImplementedError' if cycle=='edit_test' else 'return n - 1')+'\n')
            prompt=('Implement increment(n) as n+1 in math_ops.py and run the tests.' if cycle=='edit_test' else 'The test suite fails. Run it, investigate the cause, fix the source and rerun it. Do not modify tests.')+f' Test command: {py} -m pytest -q -p no:cacheprovider'
        before=hashes(work) if cycle!='read' else {}
        result=run(work,prompt,s['kind'],s['model_id'],timeout=600)
        tools=[e['part'] for e in result['events'] if e.get('type')=='tool_use'];texts=[e['part'].get('text','') for e in result['events'] if e.get('type')=='text']
        if cycle=='read':ok=any(t.get('tool')=='read' and t.get('state',{}).get('status')=='completed' for t in tools) and 'NATIVE-M3-4829' in ''.join(texts);acceptance=None
        else:
            acceptance=grade(work,f'{py} -m pytest -q -p no:cacheprovider')
            shell=any(t.get('tool')=='bash' and t.get('state',{}).get('status')=='completed' for t in tools)
            ok=acceptance['rc']==0 and before==hashes(work) and shell
        row={'cycle':cycle,'pass':ok and not result['timeout'],'acceptance':acceptance,'agent':result,'tools':[t.get('tool') for t in tools]};rows.append(row)
        dest.write_text(json.dumps({'server':s,'rows':rows,'passed':sum(x['pass'] for x in rows)},indent=2)+'\n');print(cycle,row['pass'],result['wall_s'],dest,flush=True)
        if not row['pass']:break
if __name__=='__main__':main()
