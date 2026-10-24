"""Generate static reviewable configs; launcher re-resolves the served model ID."""
import json
from opencode_local import ROOT,configuration
manifest=json.loads((ROOT/'models/manifest.json').read_text())
for kind,model in [('mlx',manifest['path']),('bonsai','bonsai'),('gguf','gguf')]:
    cfg,_=configuration(kind,model)
    (ROOT/f'opencode/configs/{kind}.json').write_text(json.dumps(cfg,indent=2)+'\n')
print('Wrote 3 isolated configs (GGUF pending runtime validation).')
