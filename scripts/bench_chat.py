"""D062 chat-mode check: single-turn prompts, no tools, profile from LAB_PROFILE. Generation only: grading runs
after the server stops (grade_chat.py), so build/test tooling never shares memory with the model."""
import datetime,json
from bench_api import request
from server import ROOT,load_profile

REPS=3
def finish(events):
    r=[c['finish_reason'] for e in events for c in e['event'].get('choices',[]) if c.get('finish_reason')]
    return r[-1] if r else None

def main():
    s=json.loads((ROOT/'logs/server.json').read_text());p=load_profile();base=f"http://127.0.0.1:{s['port']}/v1"
    tasks=json.loads((ROOT/'benchmarks/chat/tasks.json').read_text())['tasks'];rows=[]
    out=ROOT/'benchmarks/results'/f"chat-{s['kind']}-{datetime.datetime.now():%Y%m%dT%H%M%S}.json"
    for rep in range(1,REPS+1):
        for t in tasks:
            body={'model':s['model_id'],'messages':[{'role':'user','content':(ROOT/f"benchmarks/chat/prompts/{t['id']}.md").read_text()}],
                  'stream':True,'stream_options':{'include_usage':True},'temperature':p['temperature'],'top_p':p['top_p'],'max_tokens':p['output']}
            try:r=request(base,body,timeout=1800)
            except Exception as e:r={'error':repr(e)}  # infrastructure, reported apart from quality
            r.update({'task':t['id'],'rep':rep,'finish_reason':finish(r.get('events',[])),'request':body});rows.append(r)
            out.write_text(json.dumps({'schema':1,'decision':'D062','server':s,'profile':p,'rows':rows})+'\n')
            print(t['id'],rep,round(r.get('wall_s',0)),r['finish_reason'],(r.get('timings') or {}).get('predicted_per_second'),r.get('error',''),flush=True)
    print(out)

if __name__=='__main__':main()
