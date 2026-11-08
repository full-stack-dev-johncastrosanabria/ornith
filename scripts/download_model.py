"""Pinned HF download, shared cache, minimum free disk reserve; no inference."""
import json
import shutil
import sys
import threading
import time
import urllib.request
import argparse
from pathlib import Path
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
REPO = 'ornith-ai/Ornith-1.5-9B-MLX-4bit'
REV = 'a48173b246ac705be75c05bedf1a0666db522d53'
RESERVE = 8 * 1024**3
PATTERNS = ['*.json', '*.safetensors', '*.jinja']
# Pinned comparison candidates: repo, revision, file patterns, models/ link name.
CANDIDATES = {
    'qwen': ('mlx-community/Qwen3.5-9B-MLX-4bit', '938d8919941c6e7efd3c7150eff7fe9d12afa631', PATTERNS, 'qwen3.5-9b-mlx'),
    'granite': ('mlx-community/granite-4.1-8b-4bit', '08fb1e272f7bd49fa83ce279bbdc496c980380ac', PATTERNS, 'granite-4.1-8b-mlx'),
    'bonsai9': ('prism-ml/Ternary-Bonsai-2-9B-gguf', '82265ccc78ddaac4700286a35e9badcc32376dd9', ['Ternary-Bonsai-2-9B-PTQ1_0.gguf'], 'bonsai2-9b.gguf'),
    'gemma': ('lmstudio-community/gemma-4-12B-it-MLX-4bit', 'f45bda5639cf187cd5f127a5484813f5f1e3a6ad', PATTERNS, 'gemma-4-12b-mlx'),
    # SERA-8B (GLM-4.6 teacher) has no MLX 4-bit build; only the -GA variant does.
    'sera8': ('bartowski/allenai_SERA-8B-GGUF', '4c69384f86828c5f54a5ac3116450ecafdd099c8', ['allenai_SERA-8B-Q4_K_M.gguf'], 'sera-8b.gguf'),
}

def main():
    import fnmatch
    ap=argparse.ArgumentParser();ap.add_argument('--gguf',action='store_true');ap.add_argument('--candidate',choices=CANDIDATES);args=ap.parse_args()
    repo,rev,patterns=REPO,REV,PATTERNS;name='ornith-gguf.gguf' if args.gguf else 'ornith-mlx'
    if args.gguf:repo,rev,patterns='ornith-ai/Ornith-1.5-9B-GGUF','abdd624b12ebf020b767fff532ff44fe552b28c3',['Ornith-1.5-9B-Q4_K_M.gguf']
    if args.candidate:repo,rev,patterns,name=CANDIDATES[args.candidate]
    single=name.endswith('.gguf')
    data = json.load(urllib.request.urlopen(f'https://huggingface.co/api/models/{repo}/revision/{rev}?blobs=true'))
    files = [f for f in data['siblings'] if any(fnmatch.fnmatch(f['rfilename'], p) for p in patterns)]
    assert files, 'Pinned repository returned no selected model files.'
    cache = Path.home()/'.cache/huggingface/hub'/('models--'+repo.replace('/', '--'))/'snapshots'/rev
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
    path = snapshot_download(repo, revision=rev, allow_patterns=patterns, max_workers=1)
    assert all((Path(path)/f['rfilename']).stat().st_size==f['size'] for f in files), 'Downloaded file sizes do not match pinned metadata.'
    link = ROOT/'models'/name
    target=Path(path)/patterns[0] if single else Path(path)
    if link.exists() or link.is_symlink():
        if link.resolve()!=target.resolve():raise FileExistsError(f'Preserving existing model path: {link}')
    else:link.symlink_to(target,target_is_directory=not single)
    manifest=ROOT/('models/manifest-'+args.candidate+'.json' if args.candidate else 'models/manifest-gguf.json' if args.gguf else 'models/manifest.json')
    manifest.write_text(json.dumps({'repo':repo,'revision':rev,'path':str(target)},indent=2)+'\n')
    print(path, flush=True)

if __name__ == '__main__': main()
