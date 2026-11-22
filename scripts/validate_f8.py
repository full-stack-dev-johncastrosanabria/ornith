"""D061: every F8 fixture must fail at baseline and pass with its reference overlay, graded exactly as bench_tasks grades."""
import datetime,json,pathlib,shutil,sys,uuid
from bench_tasks import grade,hashes,restore
from opencode_local import WORK
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/'benchmarks/fixtures';REF=ROOT/'benchmarks/reference'

def main(selected):
    manifest=json.loads((BASE/'manifest.json').read_text())
    out={'protocol':'D061 fixture validation','started':datetime.datetime.now().isoformat(),'rows':[]}
    for spec in [r for r in manifest['tasks'] if r['task'].startswith('F8-') and (not selected or r['task'] in selected)]:
        t=spec['task'];work=WORK/f'validate-{t}-{uuid.uuid4().hex[:8]}';shutil.copytree(BASE/t,work)
        error=restore(work)
        if error:out['rows'].append({'task':t,'ok':False,'restore':error[-2000:]});print(t,'restore failed');continue
        before=hashes(work);base=grade(work,spec['command'])
        # Fresh mtimes: copy2 would keep the overlay older than the baseline build and MSBuild would reuse it.
        shutil.copytree(REF/t,work,dirs_exist_ok=True,copy_function=shutil.copy)
        ref=grade(work,spec['command']);unchanged=before==hashes(work)
        row={'task':t,'baseline_rc':base['rc'],'reference_rc':ref['rc'],'baseline_wall_s':round(base['wall_s'],1),'reference_wall_s':round(ref['wall_s'],1),
             'tests_unchanged':unchanged,'ok':base['rc'] not in (0,124) and ref['rc']==0 and unchanged,
             'baseline_tail':(base['stdout']+base['stderr'])[-1200:],'reference_tail':(ref['stdout']+ref['stderr'])[-1200:]}
        for neg in sorted(REF.glob(f'{t}.neg-*')):
            # D061 negative controls: a forbidden shortcut must not pass.
            w=WORK/f'validate-{neg.name}-{uuid.uuid4().hex[:8]}';shutil.copytree(BASE/t,w);restore(w)
            shutil.copytree(neg,w,dirs_exist_ok=True,copy_function=shutil.copy);g=grade(w,spec['command'])
            row.setdefault('negatives',{})[neg.name]=g['rc'];row['ok']&=g['rc'] not in (0,124);shutil.rmtree(w)
        out['rows'].append(row);print(t,'ok' if row['ok'] else 'BAD',row['baseline_rc'],row['reference_rc'],row['baseline_wall_s'],row['reference_wall_s'],row.get('negatives',''),flush=True)
        shutil.rmtree(work)
    out['all_ok']=all(r['ok'] for r in out['rows'])
    p=ROOT/f"benchmarks/results/f8-validation-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.json";p.write_text(json.dumps(out,indent=2)+'\n')
    print('ALL OK' if out['all_ok'] else 'FAILURES',p)
    raise SystemExit(0 if out['all_ok'] else 1)

if __name__=='__main__':main(sys.argv[1:])
