"""One native inference server at a time, with owned process-group shutdown."""
import argparse
import json
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from memory import require_space

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT/'logs/server.json'
LOCK = ROOT/'logs/inference.lock'
BONSAI = pathlib.Path.home()/'Library/Mobile Documents/com~apple~CloudDocs/bonsai/bonsai-demo'
PORTS = {'mlx':8082, 'gguf':8083, 'bonsai':8085}

def active():
    # 8080 belongs to an unrelated existing service, outside this laboratory.
    # Do not send experimental traffic there or stop its owner.
    for port in [8082,8083,8084,8085,11434,1234]:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(('127.0.0.1',port)) == 0:
                raise RuntimeError(f'Port {port} active; stop the other server explicitly first.')
    p = subprocess.check_output(['ps','-axo','pid,args'],text=True)
    for line in p.splitlines():
        if any(x in line.lower() for x in ['llama-server','mlx_lm.server','mlx_lm server','scripts/mlx_server.py','ollama serve']):
            raise RuntimeError(f'Existing inference process: {line.strip()}')

def start(kind):
    require_space()
    ROOT.joinpath('logs').mkdir(exist_ok=True)
    active()
    fd=os.open(LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    os.close(fd)
    env=os.environ.copy();env['HF_HUB_OFFLINE']='1';env['HF_HUB_DISABLE_TELEMETRY']='1'
    port=PORTS[kind]
    profile=json.loads((ROOT/'runtimes/profile.json').read_text())
    if kind=='mlx':
        model=ROOT/'models/ornith-mlx'
        if not model.exists():LOCK.unlink();raise RuntimeError('Run download_model.py first.')
        cmd=[str(ROOT/'runtimes/mlx/.venv/bin/python'),str(ROOT/'scripts/mlx_server.py'),'--model',str(model),'--host','127.0.0.1','--port',str(port),'--temp','0.6','--top-p','0.95','--max-tokens','1024','--decode-concurrency','1','--prompt-concurrency','1','--prompt-cache-size','1','--prompt-cache-bytes','536870912']
    else:
        if kind=='bonsai':
            binary=BONSAI/'bin/mac/llama-server';model=BONSAI/'models/bonsai2-gguf/27B/Ternary-Bonsai-2-27B-PTQ1_0.gguf'
        else:
            binary=ROOT/'runtimes/gguf/llama.cpp/build/bin/llama-server';model=ROOT/'models/ornith-gguf.gguf'
        if not binary.exists() or not model.exists():LOCK.unlink();raise RuntimeError('Missing local binary/weights; no automatic download.')
        cmd=[str(binary),'-m',str(model),'--alias',kind,'--host','127.0.0.1','--port',str(port),'-ngl','99','-fa','on','-c',str(profile['context']),'-np','1','--jinja','--temp','0.6','--top-p','0.95','--top-k','0','--min-p','0']
        if kind=='bonsai':cmd+=['--reasoning-budget','100','--cache-ram','512']
    try:
        with (ROOT/f'logs/{kind}-server.log').open('ab') as log:
            p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=log,start_new_session=True)
        state={'kind':kind,'pid':p.pid,'port':port,'cmd':cmd,'started':time.time(),'profile':profile}
        STATE.write_text(json.dumps(state,indent=2)+'\n')
        for _ in range(240):
            if p.poll() is not None:raise RuntimeError(f'Server exited {p.returncode}; see logs/{kind}-server.log')
            try:
                d=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/v1/models',timeout=2))
                ids=[m['id'] for m in d['data']]
                chosen=next((m for m in ids if m==str(model)),ids[0])
                state['model_id']=chosen;state['models']=ids;STATE.write_text(json.dumps(state,indent=2)+'\n')
                print(json.dumps(state));return
            except Exception:time.sleep(1)
        raise RuntimeError('Model did not become ready within 240 seconds')
    except BaseException:
        if STATE.exists():stop()
        elif LOCK.exists():LOCK.unlink()
        raise

def stop():
    if not STATE.exists():
        if LOCK.exists():raise RuntimeError('Orphan lock: inspect processes before removing it.')
        print('No owned server.');return
    s=json.loads(STATE.read_text());pid=s['pid']
    command=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
    identity=s['cmd'][:2] if 'python' in pathlib.Path(s['cmd'][0]).name else s['cmd'][:1]
    if command.strip() and not all(part in command for part in identity):raise RuntimeError('PID reused; refusing to signal unrelated process.')
    if command.strip():
        os.killpg(pid,signal.SIGTERM)
        for _ in range(60):
            with socket.socket() as c:
                if c.connect_ex(('127.0.0.1',s['port']))!=0:break
            time.sleep(.5)
        else:raise RuntimeError('Server still owns port; manual inspection required.')
    STATE.unlink();LOCK.unlink(missing_ok=True);print('Owned server stopped.')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['start','stop','status']);ap.add_argument('kind',nargs='?',choices=PORTS)
    a=ap.parse_args()
    if a.action=='start':
        if not a.kind:ap.error('kind is required for start')
        start(a.kind)
    elif a.action=='stop':stop()
    else:print(STATE.read_text() if STATE.exists() else 'No owned server.')
