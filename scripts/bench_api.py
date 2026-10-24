"""Serial short SSE benchmark. Raw events retained; never infer prefill from TTFT."""
import argparse,datetime,json,pathlib,statistics,time,urllib.request,uuid
from memory import snapshot
ROOT=pathlib.Path(__file__).resolve().parents[1]

def request(base,body,timeout=900):
    req=urllib.request.Request(base+'/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    t=time.perf_counter();first=None;last=None;tool=None;events=[];text='';reasoning='';usage={};timings={};toolcalls=[]
    with urllib.request.urlopen(req,timeout=timeout) as response:
        for line in response:
            if not line.startswith(b'data:'):continue
            raw=line[5:].strip()
            if raw==b'[DONE]':break
            d=json.loads(raw);elapsed=time.perf_counter()-t;events.append({'s':elapsed,'event':d})
            usage=d.get('usage') or usage;timings=d.get('timings') or timings
            for c in d.get('choices',[]):
                delta=c.get('delta',{})
                if delta.get('content') or delta.get('reasoning') or delta.get('reasoning_content') or delta.get('tool_calls'):
                    first=elapsed if first is None else first;last=elapsed
                text+=delta.get('content') or '';reasoning+=delta.get('reasoning') or delta.get('reasoning_content') or ''
                if delta.get('tool_calls'):
                    tool=elapsed if tool is None else tool;toolcalls+=delta['tool_calls']
    total=time.perf_counter()-t
    return {'wall_s':total,'ttft_s':first,'first_tool_delta_s':tool,'content':text,'reasoning':reasoning,'usage':usage,'timings':timings,'tool_calls_deltas':toolcalls,'events':events}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repeats',type=int,default=3);ap.add_argument('--max-tokens',type=int,default=128);a=ap.parse_args()
    s=json.loads((ROOT/'logs/server.json').read_text());base=f"http://127.0.0.1:{s['port']}/v1"
    rows=[]
    for i in range(a.repeats):
        before=snapshot()
        body={'model':s['model_id'],'messages':[{'role':'user','content':f'Run {uuid.uuid4().hex}. Write only a Python function that returns the sorted unique integers from a list, with a docstring and three examples.'}],'stream':True,'stream_options':{'include_usage':True},'temperature':.6,'top_p':.95,'max_tokens':a.max_tokens,'cache_prompt':False}
        row=request(base,body);row.update({'repeat':i+1,'memory_before':before,'memory_after':snapshot(),'request':body});rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k in ['repeat','wall_s','ttft_s','usage','timings']}),flush=True)
    out={'schema':1,'server':s,'protocol':'fresh nonce at prompt start, cache_prompt=false (runtime support varies), sequential, no warmup discarded','rows':rows,'medians':{k:statistics.median(x[k] for x in rows if x[k] is not None) for k in ['wall_s','ttft_s']}}
    p=ROOT/'benchmarks/results'/f"micro-{s['kind']}-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.json";p.write_text(json.dumps(out,indent=2)+'\n');print(p)

if __name__=='__main__':main()
