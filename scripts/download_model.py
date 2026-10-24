"""Pinned HF download, shared cache, minimum free disk reserve; no inference."""
import json
import shutil
import sys
import threading
import time
import urllib.request
from pathlib import Path
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
REPO = 'ornith-ai/Ornith-1.5-9B-MLX-4bit'
REV = 'a48173b246ac705be75c05bedf1a0666db522d53'
RESERVE = 8 * 1024**3
PATTERNS = ['*.json', '*.safetensors', '*.jinja']

def main():
    import fnmatch
    data = json.load(urllib.request.urlopen(f'https://huggingface.co/api/models/{REPO}/revision/{REV}?blobs=true'))
    files = [f for f in data['siblings'] if any(fnmatch.fnmatch(f['rfilename'], p) for p in PATTERNS)]
    cache = Path.home()/'.cache/huggingface/hub'/('models--'+REPO.replace('/', '--'))/'snapshots'/REV
    missing = sum(f.get('size', 0) for f in files if not (cache/f['rfilename']).exists())
    free = shutil.disk_usage(ROOT).free
    print(json.dumps({'free_bytes': free, 'missing_bytes': missing, 'reserve_bytes': RESERVE}), flush=True)
    if free - missing < RESERVE:
        sys.exit('Insufficient disk: download refused; preserve 8 GiB reserve.')
    def watch():
        while True:
            if shutil.disk_usage(ROOT).free < RESERVE:
                print('Disk reserve breached; aborting download.', file=sys.stderr, flush=True)
                __import__('os')._exit(75)
            time.sleep(1)
    threading.Thread(target=watch, daemon=True).start()
    path = snapshot_download(REPO, revision=REV, allow_patterns=PATTERNS, max_workers=1)
    link = ROOT/'models/ornith-mlx'
    if not link.exists(): link.symlink_to(path, target_is_directory=True)
    (ROOT/'models/manifest.json').write_text(json.dumps({'repo': REPO, 'revision': REV, 'path': path}, indent=2)+'\n')
    print(path, flush=True)

if __name__ == '__main__': main()
