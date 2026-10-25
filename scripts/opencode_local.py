"""Isolated OpenCode v1 launcher, enforced native macOS workspace/network sandbox."""
import argparse,json,os,pathlib,shutil,signal,subprocess,time,uuid,threading
from server import PORTS
ROOT=pathlib.Path(__file__).resolve().parents[1]

def configuration(kind,model_id,harness=''):
    profile=json.loads((ROOT/'runtimes/profile.json').read_text())
    provider={'mlx':'ornith-mlx','gguf':'ornith-gguf','bonsai':'bonsai-gguf'}[kind]
    port=PORTS[kind]
    ref=provider+'/local'
    permissions={'*':'deny',**{t:'allow' for t in ['read','glob','grep','edit','bash']},'external_directory':'deny'}
    prompt='You are a local programming agent. Work only in the current workspace. Read relevant files, make minimal changes, run the available tests, and report actual results. Never modify acceptance tests. Never use the network. Do not delegate.'
    cfg={'$schema':'https://opencode.ai/config.json','model':ref,'small_model':ref,'enabled_providers':[provider],'autoupdate':False,'share':'disabled','snapshot':False,'plugin':[],'mcp':{},'lsp':False,'formatter':False,'permission':permissions,'compaction':{'auto':True,'prune':True,'reserved':1536},'provider':{provider:{'npm':'@ai-sdk/openai-compatible','name':provider,'options':{'baseURL':f'http://127.0.0.1:{port}/v1','apiKey':'local-only'},'models':{'local':{'id':model_id,'name':model_id,'tool_call':True,'limit':{'context':8192,'output':1536}}}}},'default_agent':'ornith-code','agent':{'ornith-code':{'description':'Local workspace coding agent','mode':'primary','model':ref,'temperature':.6,'top_p':.95,'steps':12,'prompt':prompt+('\n'+harness if harness else ''),'permission':permissions},'title':{'disable':True},'summary':{'disable':True}}}
    cfg['provider'][provider]['models']['local']['limit']={'context':profile['context'],'output':profile['output']}
    return cfg,ref

def sandbox(work,state):
    # macOS Seatbelt: deny home data outside explicit paths; no external network.
    home=pathlib.Path.home();q=lambda s:json.dumps(str(s))
    reads=[work,state,ROOT/'opencode/configs',ROOT/'runtimes/mlx/.venv',ROOT/'harness2/.venv',ROOT/'benchmarks/.venv',home/'.local/share/uv/python',home/'.nuget/packages']
    profile='(version 1)\n(allow default)\n(deny network*)\n'
    profile+='(allow network-outbound (remote ip "localhost:*"))\n(allow network-inbound (local ip "localhost:*"))\n(allow network-bind (local ip "localhost:*"))\n'
    profile+=f'(deny file-read-data (subpath {q(home)}))\n'
    for p in reads:profile+=f'(allow file-read-data (subpath {q(p.resolve())}))\n'
    profile+=f'(allow file-read-data (literal {q(ROOT/"AGENTS.md")}))\n'
    profile+='(deny file-write*)\n'
    for p in [work,state]:profile+=f'(allow file-write* (subpath {q(p.resolve())}))\n'
    profile+=f'(deny file-write* (subpath {q(work/"tests")}))\n'
    for p in [work/'tests/obj',work/'tests/bin']:profile+=f'(allow file-write* (subpath {q(p)}))\n'
    profile+='(allow file-write-data (literal "/dev/null") (literal "/dev/tty"))\n'
    return profile

def prepare(work,kind,model_id,harness=''):
    work=pathlib.Path(work).resolve()
    if not work.is_relative_to(ROOT/'benchmarks/work'):raise ValueError('Workspace must be inside benchmarks/work')
    state=ROOT/'opencode/state'/uuid.uuid4().hex
    for d in ['config','data','cache','state','tmp']: (state/d).mkdir(parents=True,exist_ok=True)
    # Empty isolated NuGet state has nothing to migrate. Its sentinel avoids the
    # runtime's hardcoded /tmp/.dotnet.* migration mutex without relaxing writes.
    migrations=state/'data/NuGet/Migrations';migrations.mkdir(parents=True);(migrations/'1').touch()
    cfg,ref=configuration(kind,model_id,harness)
    config=state/'config/opencode.json';config.write_text(json.dumps(cfg,indent=2)+'\n')
    # Strip all inherited provider credentials and configuration, keep only native essentials.
    env={k:v for k,v in os.environ.items() if k in ['PATH','HOME','USER','LOGNAME','SHELL','LANG','TERM','SSH_AUTH_SOCK']}
    env.update({'XDG_CONFIG_HOME':str(state/'config'),'XDG_DATA_HOME':str(state/'data'),'XDG_CACHE_HOME':str(state/'cache'),'XDG_STATE_HOME':str(state/'state'),'TMPDIR':str(state/'tmp'),'OPENCODE_CONFIG':str(config),'OPENCODE_DISABLE_PROJECT_CONFIG':'true','OPENCODE_DISABLE_AUTOUPDATE':'true','OPENCODE_DISABLE_MODELS_FETCH':'true','OPENCODE_DISABLE_DEFAULT_PLUGINS':'true','OPENCODE_DISABLE_CLAUDE_CODE':'true','OPENCODE_DISABLE_EXTERNAL_SKILLS':'true','DO_NOT_TRACK':'1','HF_HUB_OFFLINE':'1'})
    env.update({'PYTHONDONTWRITEBYTECODE':'1','DOTNET_CLI_HOME':str(state/'dotnet'),'DOTNET_CLI_TELEMETRY_OPTOUT':'1','DOTNET_SKIP_FIRST_TIME_EXPERIENCE':'1','DOTNET_CLI_USE_MSBUILD_SERVER':'0','MSBUILDDISABLENODEREUSE':'1','NUGET_PACKAGES':str(pathlib.Path.home()/'.nuget/packages')})
    env.update({'DOTNET_EnableDiagnostics':'0','DOTNET_GENERATE_ASPNET_CERTIFICATE':'false','DOTNET_NOLOGO':'1','GIT_CONFIG_GLOBAL':str(state/'config/empty-gitconfig'),'GIT_CONFIG_NOSYSTEM':'1'})
    (state/'config/empty-gitconfig').touch()
    profile=state/'sandbox.sb';profile.write_text(sandbox(work,state))
    return env,profile,ref,state

def run(work,prompt,kind,model_id,harness='',timeout=1200,*,argv=None,read_roots=(),read_directories=()):
    work=pathlib.Path(work).resolve()
    env,profile,ref,state=prepare(work,kind,model_id,harness)
    if read_roots:
        profile.write_text(profile.read_text()+''.join('(allow file-read-data (subpath '+json.dumps(str(pathlib.Path(p).resolve()))+'))\n' for p in read_roots))
    if read_directories:
        profile.write_text(profile.read_text()+''.join('(allow file-read-data (literal '+json.dumps(str(pathlib.Path(p).resolve()))+'))\n' for p in read_directories))
    env['BUN_INSTALL_CACHE_DIR']=str(state/'cache/bun')
    cmd=['/usr/bin/sandbox-exec','-f',str(profile)]+(argv or [shutil.which('opencode'),'run',prompt,'--dir',str(work),'--agent','ornith-code','--model',ref,'--format','json','--title','local-lab','--pure'])
    started_epoch_ms=int(time.time()*1000)
    t=time.perf_counter();events=[];timed_out=False;samples=[];resource_abort=[];done=threading.Event()
    def sample():
        from memory import snapshot
        while not done.is_set():
            row=snapshot();row['elapsed_s']=time.perf_counter()-t
            if (ROOT/'logs/server.json').exists():
                pid=json.loads((ROOT/'logs/server.json').read_text())['pid']
                row['server_rss_kib']=subprocess.run(['ps','-p',str(pid),'-o','rss='],capture_output=True,text=True).stdout.strip()
            samples.append(row);done.wait(5)
            if row['disk_free_bytes']<8*1024**3 and p.poll() is None:
                resource_abort.append('disk below 8 GiB reserve');os.killpg(p.pid,signal.SIGTERM);return
    sampler=threading.Thread(target=sample,daemon=True)
    with (state/'stdout.jsonl').open('w') as out,(state/'stderr.log').open('w') as err:
        p=subprocess.Popen(cmd,cwd=work,env=env,stdout=out,stderr=err,start_new_session=True)
        sampler.start()
        (state/'process.json').write_text(json.dumps({'pid':p.pid,'pgid':p.pid,'argv':cmd},indent=2)+'\n')
        try:p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True;os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=15)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=15)
    done.set();sampler.join(timeout=5)
    for line in (state/'stdout.jsonl').read_text().splitlines():
        try:events.append(json.loads(line))
        except json.JSONDecodeError:pass
    result={'rc':p.returncode,'timeout':timed_out,'wall_s':time.perf_counter()-t,'started_epoch_ms':started_epoch_ms,'state':str(state),'events':events,'memory_samples':samples,'stderr':(state/'stderr.log').read_text()[-8000:],'configuration_sha256':__import__('hashlib').sha256((state/'config/opencode.json').read_bytes()).hexdigest()}
    result['resource_abort']=resource_abort
    (state/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('workspace',type=pathlib.Path);ap.add_argument('prompt',nargs='?',default='Read README.md and report its contents.');ap.add_argument('--timeout',type=int,default=1200);a=ap.parse_args()
    s=json.loads((ROOT/'logs/server.json').read_text());result=run(a.workspace,a.prompt,s['kind'],s['model_id'],timeout=a.timeout)
    print(json.dumps(result,indent=2));raise SystemExit(result['rc'] or 0)
