"""Native memory snapshot; initial swap is not attributed to the model."""
import datetime,json,subprocess,shutil
def snapshot():
    out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'disk_free_bytes':shutil.disk_usage(__file__).free}
    for key,cmd in [('vm_stat',['vm_stat']),('swap',['sysctl','vm.swapusage']),('pressure',['memory_pressure','-Q'])]:
        p=subprocess.run(cmd,capture_output=True,text=True)
        out[key]=p.stdout.strip()
    return out
if __name__=='__main__': print(json.dumps(snapshot(),indent=2))
