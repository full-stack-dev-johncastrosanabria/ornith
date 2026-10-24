"""Verify file/test protection and non-loopback denial before agent execution."""
import json,pathlib,subprocess,sys,uuid
from opencode_local import prepare
ROOT=pathlib.Path(__file__).resolve().parents[1]
work=ROOT/'benchmarks/work'/('sandbox-'+uuid.uuid4().hex[:8]);(work/'tests').mkdir(parents=True)
(work/'read.txt').write_text('readable');(work/'tests/test.txt').write_text('immutable')
env,profile,ref,state=prepare(work,'mlx','unused')
code='''import pathlib,socket,json
w=pathlib.Path.cwd(); results={}
results['workspace_read']=w.joinpath('read.txt').read_text()=='readable'
w.joinpath('writable.txt').write_text('ok');results['workspace_write']=True
for name,path in [('outside_read',pathlib.Path.home()/'.config/opencode/opencode.jsonc'),('tests_write',w/'tests/test.txt'),('outside_write',w.parent/'escape.txt')]:
 try:
  if name.endswith('read'):path.read_text()
  else:path.write_text('BAD')
  results[name+'_denied']=False
 except PermissionError:results[name+'_denied']=True
try:
 s=socket.create_connection(('1.1.1.1',443),timeout=2);s.close();results['external_network_denied']=False
except PermissionError:results['external_network_denied']=True
print(json.dumps(results))
'''
p=subprocess.run(['/usr/bin/sandbox-exec','-f',str(profile),sys.executable,'-c',code],cwd=work,env=env,capture_output=True,text=True)
report={'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'profile':profile.read_text()}
if p.returncode==0:report['checks']=json.loads(p.stdout)
(ROOT/'benchmarks/results/sandbox-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert p.returncode==0 and all(report['checks'].values())
