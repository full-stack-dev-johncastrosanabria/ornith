"""D051 memory gate for the D033 cap8k arm: samples every 5 s; a breach makes that model's arm infrastructure N/E."""
import json,os,pathlib,re,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]

def sample():
    free=int(re.search(r'(\d+)%',subprocess.run(['memory_pressure','-Q'],capture_output=True,text=True).stdout).group(1))
    swap=float(re.search(r'used = ([\d.,]+)M',subprocess.run(['sysctl','-n','vm.swapusage'],capture_output=True,text=True).stdout).group(1).replace(',','.'))
    try:kind=json.loads((ROOT/'logs/server.json').read_text())['kind']
    except Exception:kind=None
    return {'t':time.time(),'kind':kind,'free_pct':free,'swap_mb':swap}

def breaches(samples):
    """Per kind: 3 consecutive samples below 10 % free, or swap growth > 2 GiB over that kind's first sample."""
    out={};first={};low={};prev=None
    for s in samples:
        k=s['kind']
        if k is None:continue
        # D061 (n): a resumed arm (another kind ran in between) starts a new segment with its own baseline.
        if k!=prev:first[k]=s['swap_mb'];low[k]=0;prev=k
        low[k]=low[k]+1 if s['free_pct']<10 else 0
        if low[k]>=3:out.setdefault(k,'memory_pressure free <10 % for 3 samples')
        if s['swap_mb']-first[k]>2048:out.setdefault(k,'swap grew >2 GiB over arm start')
    return out

assert breaches([{'kind':'a','free_pct':5,'swap_mb':0}]*3)=={'a':'memory_pressure free <10 % for 3 samples'}
assert breaches([{'kind':'a','free_pct':50,'swap_mb':100},{'kind':'a','free_pct':50,'swap_mb':2200}])=={'a':'swap grew >2 GiB over arm start'}
assert breaches([{'kind':'a','free_pct':5,'swap_mb':0},{'kind':'a','free_pct':50,'swap_mb':0},{'kind':'a','free_pct':5,'swap_mb':0}])=={}
assert breaches([{'kind':'a','free_pct':50,'swap_mb':100},{'kind':'b','free_pct':50,'swap_mb':5000},{'kind':None,'free_pct':50,'swap_mb':5000},{'kind':'a','free_pct':50,'swap_mb':5000}])=={}
assert breaches([{'kind':'a','free_pct':50,'swap_mb':100},{'kind':None,'free_pct':50,'swap_mb':100},{'kind':'a','free_pct':50,'swap_mb':2200}])=={'a':'swap grew >2 GiB over arm start'}

if __name__=='__main__':
    log=ROOT/f'logs/memory-gate-{sys.argv[1]}.jsonl'
    while True:
        with log.open('a') as f:f.write(json.dumps(sample())+'\n')
        time.sleep(5)
