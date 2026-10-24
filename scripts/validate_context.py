"""Single long-prefill stability probe, not a quality or agent benchmark."""
import datetime,json,pathlib,threading,time,urllib.request
from bench_api import request
from memory import snapshot
ROOT=pathlib.Path(__file__).resolve().parents[1]
s=json.loads((ROOT/'logs/server.json').read_text());base=f"http://127.0.0.1:{s['port']}/v1";samples=[];done=threading.Event()
def sample():
    while not done.is_set():samples.append(snapshot());done.wait(5)
t=threading.Thread(target=sample,daemon=True);t.start()
body={'model':s['model_id'],'messages':[{'role':'user','content':'After this padding, reply only OK.\n'+'padding '*12000+'\nReply OK.'}],'temperature':.6,'top_p':.95,'max_tokens':128,'stream':True,'stream_options':{'include_usage':True}}
try:result=request(base,body)
finally:done.set();t.join(timeout=5)
health=json.load(urllib.request.urlopen(f"http://127.0.0.1:{s['port']}/health"))
out={'purpose':'one long-prefill native stability probe; not an agent/quality score','server':s,'request':body,'response':result,'memory_samples':samples,'health_after':health}
p=ROOT/'benchmarks/results'/f"context-stability-{s['profile']['context']}-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.json";p.write_text(json.dumps(out,indent=2)+'\n');print(p);print(result['usage'],result['wall_s'],health);assert health['status']=='ok' and result['usage'].get('prompt_tokens',0)>8192
