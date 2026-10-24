"""Check the conditional GGUF phase without downloading anything."""
import datetime,json,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
needed=5780090816;free=shutil.disk_usage(ROOT).free;reserve=8*1024**3
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo':'ornith-ai/Ornith-1.5-9B-GGUF','revision':'abdd624b12ebf020b767fff532ff44fe552b28c3','file':'Ornith-1.5-9B-Q4_K_M.gguf','weight_bytes':needed,'free_bytes':free,'reserve_bytes':reserve,'projected_free_bytes':free-needed,'fits_weights_only':free-needed>=reserve,'runtime_build_bytes':'additional, not included','download_performed':False}
(ROOT/'benchmarks/results/gguf-space-gate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
