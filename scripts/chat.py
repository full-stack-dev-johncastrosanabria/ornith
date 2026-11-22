#!/usr/bin/env python3
"""D066: terminal chat with a model of the local router (127.0.0.1:8099), the same raw single-turn setting D064
measured (no system prompt, temp .6, top_p .95, 4096 output). Usage: ornith-chat [model] (default GPT-OSS 20B).
Commands: /nuevo starts a new conversation, /salir exits."""
import json,sys,urllib.error,urllib.request
URL='http://127.0.0.1:8099/v1/chat/completions'
model=sys.argv[1] if len(sys.argv)>1 else 'gpt-oss-20b-mxfp4-q8'
hist=[]
print(f'{model} · la primera respuesta incluye cargar el modelo (~1 min) · /nuevo, /salir')
while True:
    try:q=input('\n> ').strip()
    except (EOFError,KeyboardInterrupt):break
    if q in ('/salir','/exit'):break
    if q=='/nuevo':hist=[];print('(conversación nueva)');continue
    if not q:continue
    hist.append({'role':'user','content':q})
    # shortcut: same ~40K-character cap as the router's trim(), keeps GPT-OSS under its measured OOM point.
    while sum(len(m['content']) for m in hist)>40000 and len(hist)>1:del hist[0]
    body={'model':model,'messages':hist,'stream':True,'temperature':.6,'top_p':.95,'max_tokens':4096}
    out='';print('(pensando…)',end='',flush=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(URL,json.dumps(body).encode(),{'Content-Type':'application/json'}),timeout=1800) as r:
            for line in r:
                if line.startswith(b'data: ') and line.strip()!=b'data: [DONE]':
                    for ch in json.loads(line[6:]).get('choices',[]):
                        if t:=(ch.get('delta') or {}).get('content'):
                            if not out:print('\r'+' '*12+'\r',end='')
                            print(t,end='',flush=True);out+=t
    except KeyboardInterrupt:print('\n(interrumpido)')
    except urllib.error.HTTPError as e:print('\nError del router:',e.read().decode(errors='replace'))
    except OSError as e:print('\nNo se pudo contactar con el router en 127.0.0.1:8099:',e)
    if out:print();hist.append({'role':'assistant','content':out})
    else:hist.pop();print('\r(sin respuesta: se agotaron los 4096 tokens pensando o hubo un error; prueba una pregunta más concreta)')
