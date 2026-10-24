"""Concise experiment status from checkpoints, without dumping traces."""
import json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
print('SERVER', (ROOT/'logs/server.json').read_text() if (ROOT/'logs/server.json').exists() else 'stopped')
for pattern in ['smoke-agent-*','tasks-*','harness-local-*','micro-*']:
    for p in sorted((ROOT/'benchmarks/results').glob(pattern+'.json')):
        d=json.loads(p.read_text())
        if pattern=='tasks-*':print(p.name,[(r['task'],r['status'],round(r.get('agent',{}).get('wall_s',0),1)) for r in d['rows']])
        elif pattern=='smoke-agent-*':print(p.name,'passed',d.get('passed'))
        elif pattern=='harness-local-*':print(p.name,'stages',list(d),'optimization_wall_s',d.get('optimization_wall_s'))
        else:print(p.name,'repetitions',len(d.get('rows',[])),'medians',d.get('medians'))
print(subprocess.check_output(['sysctl','vm.swapusage'],text=True).strip())
