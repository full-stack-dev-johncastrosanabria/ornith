"""Launch interactive OpenCode in the same isolated native sandbox."""
import argparse,json,os,pathlib,shutil
from opencode_local import ROOT,prepare
ap=argparse.ArgumentParser();ap.add_argument('kind',choices=['mlx','gguf','bonsai']);ap.add_argument('workspace',nargs='?',type=pathlib.Path);a=ap.parse_args()
s=json.loads((ROOT/'logs/server.json').read_text())
if s['kind']!=a.kind:raise SystemExit('Stop the current owned server and start the requested model first.')
work=(a.workspace or ROOT/f'benchmarks/work/interactive-{a.kind}').resolve();work.mkdir(parents=True,exist_ok=True)
env,profile,ref,state=prepare(work,a.kind,s['model_id'])
os.chdir(work)
cmd=['/usr/bin/sandbox-exec','-f',str(profile),shutil.which('opencode'),str(work),'--model',ref,'--agent','ornith-code','--pure']
os.execve(cmd[0],cmd,env)
