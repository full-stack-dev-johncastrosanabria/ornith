"""Reject an oversized request without generating tokens; check server survives."""
import json,urllib.request,urllib.error
from opencode_local import ROOT
s=json.loads((ROOT/'logs/server.json').read_text());url=f"http://127.0.0.1:{s['port']}"
context=s.get('profile',{}).get('context',8192)
body={'model':s['model_id'],'messages':[{'role':'user','content':'hello '*(context+1000)}],'max_tokens':128}
req=urllib.request.Request(url+'/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req,timeout=30) as r:out={'status':r.status,'body':r.read().decode()}
except urllib.error.HTTPError as e:out={'status':e.code,'body':e.read().decode()}
out['health']=json.load(urllib.request.urlopen(url+'/health'))
(ROOT/'benchmarks/results/context-limit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert out['status']!=200 and str(context) in out['body'] and out['health']['status']=='ok'
