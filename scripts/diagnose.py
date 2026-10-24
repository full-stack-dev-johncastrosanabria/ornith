"""Reproducible native diagnostic; excludes hardware identifiers and secrets."""
import datetime,hashlib,json,pathlib,platform,shutil,subprocess
from memory import snapshot
ROOT=pathlib.Path(__file__).resolve().parents[1]
def command(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True)
    return {'command':cmd,'rc':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()}
out={'platform':platform.platform(),'memory':snapshot(),'tools':{},'hardware':{}}
data=json.loads(subprocess.check_output(['system_profiler','SPHardwareDataType','SPDisplaysDataType','-json']))
out['hardware']={k:v for k,v in data['SPHardwareDataType'][0].items() if k in ['machine_name','machine_model','chip_type','physical_memory','number_processors']}
out['graphics']=[{k:v for k,v in g.items() if k in ['sppci_model','spdisplays_metal','spdisplays_cores','spdisplays_vendor']} for g in data['SPDisplaysDataType']]
for tool,args in [('uv',['--version']),('git',['--version']),('node',['--version']),('opencode',['--version']),('dotnet',['--list-sdks'])]:
    out['tools'][tool]={'path':shutil.which(tool),**command([tool]+args)}
out['macos']=command(['sw_vers']);out['python']=command(['uv','python','list','--only-installed'])
out['inference_processes']=[l for l in subprocess.check_output(['ps','-axo','pid,rss,comm'],text=True).splitlines() if any(t in l.lower() for t in ['llama-server','mlx_lm','ollama','opencode'])]
p=pathlib.Path.home()/'.config/opencode/opencode.jsonc'
out['global_opencode_sha256']=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
path=ROOT/'benchmarks/results'/('diagnostic-'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S')+'.json');path.write_text(json.dumps(out,indent=2)+'\n');print(path)
