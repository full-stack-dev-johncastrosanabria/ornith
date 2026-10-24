"""No-model integration checks for the official core and the local boundary."""
import json,pathlib,tempfile,unittest
from unittest.mock import patch
import harness_official as h
from harness2.core.proposer import Proposer,Reply

class ScriptedEditor(Proposer):
    def call(self,mission,context_dir,label,**kw):
        context=pathlib.Path(context_dir)
        if label.startswith('experience.'):
            reply=Reply(label=label,text='NO_ENTRY',ok=True,attempts=1)
        else:
            workspace=context/'harness';(workspace/'systemprompt.md').write_text('Read files, fix the issue, run tests, then finish promptly.\n')
            reply=Reply(label=label,text='<notes>Focused local text guidance.</notes>',ok=True,attempts=1,workspace=workspace)
        self._calls.append(reply);return reply

class OfficialTests(unittest.TestCase):
    def test_scope_and_heldout_fence(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter=h.F7Adapter(pathlib.Path(tmp))
            self.assertEqual(adapter.tasks(),['DEV'])
            self.assertFalse(list(adapter.task_files('DEV').rglob('test*')))
            with self.assertRaises(ValueError):adapter.task_prompt('F7-A')
            with self.assertRaises(ValueError):adapter.validate_tree({'scripts/escape.py':'print(1)'})

    def test_local_source_command_and_readonly_dependency_access(self):
        with patch.object(h,'require_space'),patch.object(h,'run',return_value={'executor':'','resource_abort':[]}) as runner:
            result=h.source_run(pathlib.Path('/tmp/task'),'hello','mlx','snapshot')
            argv=runner.call_args.kwargs['argv']
            self.assertEqual(argv[0],str(h.config.BUN));self.assertIn('ornith-mlx/local',argv)
            self.assertEqual(runner.call_args.kwargs['read_roots'],(h.DEP,))
            self.assertEqual(result['executor'],'official-pinned-opencode-source')
            with self.assertRaises(ValueError):h.source_run('/tmp/task','hello','bonsai','other')

    def test_real_upstream_core_drives_dev_only_with_single_workers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);adapter=h.F7Adapter(root);editor=ScriptedEditor(adapter.spec.channels['proposer'])
            def task(tid,server,harness,label,timeout):
                self.assertEqual(tid,'DEV');work=root/('work-'+str(len(list(root.glob('work-*')))));work.mkdir()
                (work/'normalize.py').write_text('def normalize(value): return value.strip()\n')
                return {'workspace':str(work),'status':'pass','artifact_acceptance':True,'agent':{'events':[{'type':'text','part':{'text':'Implemented and checked.'}}]}}
            # Limit the state-file substitution, preserving real upstream file IO.
            original=pathlib.Path.read_text
            def read_state(path,*args,**kw):return json.dumps({'kind':'mlx','model_id':'local'}) if path==h.STATE else original(path,*args,**kw)
            original_seq=h.recursion.run_sequential
            def seq(*args,**kw):
                self.assertEqual(kw['propose_workers'],1);self.assertEqual(kw['rollout_workers'],1)
                return original_seq(*args,**kw)
            with patch.object(pathlib.Path,'read_text',read_state),patch.object(h.bench_tasks,'task',side_effect=task) as solver,patch.object(h.recursion,'run_mode',h.sequential_dispatch),patch.object(h.recursion,'run_sequential',side_effect=seq):
                result=h.run_domain('programming',['DEV'],1,adapter=adapter,prop=editor,runs_root=adapter.spec.runs_root,library_root=root/'library',modes=('seq',))
            self.assertEqual(result['failed'],0,result);self.assertEqual(result['done'],1)
            self.assertEqual(solver.call_count,4)
            self.assertGreaterEqual(len(editor._calls),3)

if __name__=='__main__':unittest.main()
