"""D054 daily-use router: one local OpenAI-compatible endpoint for OpenCode. It loads the requested model on
demand with the measured lab profile (server.start/stop, one model at a time) and unloads it after IDLE_S idle."""
import http.client,json,subprocess,threading,time
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from server import PORTS,STATE,start,stop

ROUTER_PORT=8099
MODELS={'ornith-1.5-9b-q4km':'gguf','bonsai-2-27b-ptq10':'bonsai'}
IDLE_S=900
assert all(k in PORTS for k in MODELS.values())
switch=threading.Lock();last=[time.time()];busy=[0];mine=[None]

def state():return json.loads(STATE.read_text()) if STATE.exists() else None
def alive(pid):return subprocess.run(['/bin/ps','-p',str(pid)],capture_output=True).returncode==0

def ensure(kind):
    with switch:
        s=state()
        if s and s['kind']==kind and s['pid']==mine[0]:return s
        # Never touch a live server this router did not start (e.g. a lab campaign run); a dead one is stale state
        # left by a reboot or logout, and stop() only cleans its files.
        if s and s['pid']!=mine[0] and alive(s['pid']):raise RuntimeError('Another lab server is running; stop it first.')
        if s and busy[0]>1:raise RuntimeError('The other model is still answering; retry when it finishes.')
        if s:stop()
        start(kind);s=state();mine[0]=s['pid'];return s

def idle():
    while True:
        time.sleep(30)
        with switch:
            s=state()
            if s and s['pid']==mine[0] and busy[0]==0 and time.time()-last[0]>IDLE_S:stop();mine[0]=None

class Handler(BaseHTTPRequestHandler):
    def reply(self,code,data):
        self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if self.path.rstrip('/').endswith('/models'):self.reply(200,json.dumps({'object':'list','data':[{'id':m,'object':'model'} for m in MODELS]}).encode())
        else:self.reply(404,b'{}')
    def do_POST(self):
        req=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}')
        if req.get('model') not in MODELS:return self.reply(400,json.dumps({'error':f'unknown model; use one of {list(MODELS)}'}).encode())
        busy[0]+=1;sent=False
        try:
            s=ensure(MODELS[req['model']])
            c=http.client.HTTPConnection('127.0.0.1',s['port'],timeout=1800)
            c.request('POST',self.path,json.dumps({**req,'model':s['model_id']}),{'Content-Type':'application/json'})
            r=c.getresponse();self.send_response(r.status);sent=True
            for k,v in r.getheaders():
                if k.lower() not in ('transfer-encoding','connection','content-length'):self.send_header(k,v)
            self.send_header('Connection','close');self.end_headers()
            while chunk:=r.read1(65536):self.wfile.write(chunk);self.wfile.flush()
        except (Exception,SystemExit) as e:  # require_space() exits 75 when the disk reserve is low
            if not sent:self.reply(503,json.dumps({'error':str(e) or 'disk reserve'}).encode())
        finally:busy[0]-=1;last[0]=time.time()

def main():
    threading.Thread(target=idle,daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1',ROUTER_PORT),Handler).serve_forever()

if __name__=='__main__':main()
