"""Verify parsed OpenAI tool calls, execute arithmetic locally, verify follow-up."""
import datetime,json,pathlib,re,time,urllib.request
from bench_api import request
ROOT=pathlib.Path(__file__).resolve().parents[1]
def post(base,body):
    t=time.perf_counter();req=urllib.request.Request(base+'/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=600) as r:d=json.load(r)
    return d,time.perf_counter()-t
def main():
    s=json.loads((ROOT/'logs/server.json').read_text());base=f"http://127.0.0.1:{s['port']}/v1";rows=[]
    model_list=json.load(urllib.request.urlopen(base+'/models'))
    defaults={'model':s['model_id'],'temperature':.6,'top_p':.95,'max_tokens':1024}
    d,wall=post(base,{**defaults,'messages':[{'role':'user','content':'What is 17 + 25? Reply with the number only.'}]});rows.append({'test':'conversation','wall_s':wall,'response':d})
    streamed=request(base,{**defaults,'stream':True,'stream_options':{'include_usage':True},'messages':[{'role':'user','content':'Compute 13 * 7 carefully, then state the result.'}]});rows.append({'test':'streaming_reasoning','response':streamed})
    tool={'type':'function','function':{'name':'add','description':'Add two integers; call this tool to perform addition.','parameters':{'type':'object','properties':{'a':{'type':'integer'},'b':{'type':'integer'}},'required':['a','b'],'additionalProperties':False}}}
    messages=[{'role':'user','content':'Use the add tool to add 19 and 23. You must call the tool before answering.'}]
    d,wall=post(base,{**defaults,'messages':messages,'tools':[tool],'tool_choice':'auto'})
    calls=d['choices'][0]['message'].get('tool_calls',[]);row={'test':'tool_roundtrip','wall_s':wall,'response':d,'parsed_tool_calls':len(calls),'executed':False};rows.append(row)
    if calls:
        messages.append(d['choices'][0]['message'])
        for call in calls:
            assert call['function']['name']=='add'
            args=json.loads(call['function']['arguments']);assert set(args)=={'a','b'} and all(type(v) is int for v in args.values())
            value=args['a']+args['b'];assert value==42
            messages.append({'role':'tool','tool_call_id':call['id'],'content':json.dumps({'sum':value})})
        row['executed']=True
        follow,wall=post(base,{**defaults,'messages':messages,'tools':[tool]});row['followup']=follow;row['followup_wall_s']=wall
    checks={
        'conversation':bool(re.search(r'\b42\b',rows[0]['response']['choices'][0]['message'].get('content') or '')),
        'streaming':bool(re.search(r'\b91\b',streamed['content'])),
        'tool_roundtrip':row['executed'] and bool(re.search(r'\b42\b',row.get('followup',{}).get('choices',[{'message':{}}])[0]['message'].get('content') or '')),
    }
    out={'server':s,'models_response':model_list,'rows':rows,'checks':checks,'pass':all(checks.values())}
    p=ROOT/'benchmarks/results'/f"smoke-api-{s['kind']}-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.json";p.write_text(json.dumps(out,indent=2)+'\n')
    print(p);print('Parsed tool calls',len(calls),'executed',row['executed']);print('conversation',rows[0]['response']['choices'][0]['message']);print('reasoning_chars',len(streamed['reasoning']),'content',streamed['content'])
    if not out['pass']:raise SystemExit(1)
if __name__=='__main__':main()
