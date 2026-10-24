"""Install only the official pinned OpenCode/Bun substrate, inside the lab."""
import json,os,pathlib,signal,subprocess,sys,time
from memory import require_space
from server import ROOT,active

DEP=ROOT/'harness2/official/dependencies'
UP=ROOT/'harness2/upstream'

def guarded(argv,cwd=None):
    require_space()
    p=subprocess.Popen([str(a) for a in argv],cwd=cwd or ROOT,start_new_session=True)
    while p.poll() is None:
        try:require_space()
        except SystemExit:
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
            raise
        time.sleep(1)
    if p.returncode:raise subprocess.CalledProcessError(p.returncode,argv)
    require_space()

def main():
    if sys.platform!='darwin' or os.uname().machine!='arm64':raise RuntimeError('Native Apple Silicon required')
    active();require_space();DEP.mkdir(parents=True,exist_ok=True)
    # Reuse upstream setup functions, including its compatibility patch. The clean
    # Harness² reference is never edited; only a dedicated dependency checkout is patched.
    guarded([sys.executable,'-c',
        'import pathlib;from harness2 import config,install;'
        f'config.DEPENDENCIES=pathlib.Path({str(DEP)!r});config.THIRD_PARTY=pathlib.Path({str(UP/"third_party")!r});'
        'install.clone("opencode");install.patch("opencode")'])
    guarded(['npm','install','--prefix',DEP/'tools','bun@1.3.11'])
    guarded([DEP/'tools/node_modules/.bin/bun','install','--frozen-lockfile','--ignore-scripts'],cwd=DEP/'opencode')
    from harness2 import config
    info={'harness2_revision':subprocess.check_output(['git','-C',UP,'rev-parse','HEAD'],text=True).strip(),
          'opencode_revision':config.DEPENDENCY_PINS['opencode'],'bun':'1.3.11',
          'opencode_compat_patch_sha256':__import__('hashlib').sha256((UP/'third_party/patches/opencode-compat.diff').read_bytes()).hexdigest(),
          'opencode_diff':subprocess.check_output(['git','-C',DEP/'opencode','diff','--stat'],text=True)}
    (ROOT/'harness2/official/dependencies.json').write_text(json.dumps(info,indent=2)+'\n')
    print('Official substrate dependencies installed; inference has not been validated.')
if __name__=='__main__':main()
