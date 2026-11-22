"""D060 capture dry run: no model, no server; the official core must reach its first editor call."""
import json,pathlib,tempfile,unittest
from unittest.mock import patch
import h2_claude as c

class CaptureTest(unittest.TestCase):
    def test_capture_saves_the_inv_call_and_stops_the_core(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=pathlib.Path(tmp);state=tmp/'server.json';state.write_text(json.dumps({'kind':'gguf','model_id':'m'}))
            ws=tmp/'ws';ws.mkdir();(ws/'normalize.py').write_text('def normalize(x):\n    return x\n')
            calls=[]
            def task(task_id,s,harness,label,timeout):
                calls.append((task_id,label,timeout))
                return {'task':task_id,'status':'fail','workspace':str(ws),'artifact_acceptance':False,
                        'agent':{'wall_s':1.0,'events':[{'type':'text','part':{'text':'done'}}]}}
            with patch.object(c,'OUT',tmp/'out'),patch.object(c,'STATE',state),patch.object(c.bench_tasks,'task',task):
                c.capture('gguf')
            cap=tmp/'out/gguf/capture'
            self.assertTrue(calls and all(t=='DEV' for t,_,_ in calls))
            self.assertIn('---',(cap/'MISSION.md').read_text())
            self.assertTrue((cap/'context/harness/systemprompt.md').exists())
            meta=json.loads((tmp/'out/gguf/capture.json').read_text());self.assertEqual(meta['kind'],'gguf')
            self.assertEqual(len(meta['dev_rollouts']),len(calls))
            c.OUT=tmp/'out'
            try:
                c.bundle('gguf');inp=tmp/'out/gguf/input.md'
                def transcript(text):
                    rows=[{'message':{'role':'assistant','model':'claude-opus-5-5','content':[{'type':'tool_use','name':'Read','input':{'file_path':str(inp)}}]}},
                          {'message':{'role':'user','content':[{'type':'tool_result','content':''.join(f'{i+1}\t{l}\n' for i,l in enumerate(inp.read_text().splitlines()))}]}},
                          {'message':{'role':'assistant','model':'claude-opus-5-5','content':[{'type':'text','text':text}]}}]
                    t=tmp/'t.jsonl';t.write_text('\n'.join(json.dumps(r) for r in rows)+'\n');return t
                good='<<<EDIT context/harness/guardrails.md>>>\nRun the tests before finishing.\n<<<END EDIT>>>\n<<<ANSWER>>>\nok\n<<<END ANSWER>>>'
                c.ingest('gguf',transcript(good));a=json.loads((tmp/'out/gguf/audit.json').read_text())
                self.assertEqual(a['status'],'ok',a);self.assertIn('Run the tests',(tmp/'out/gguf/frozen-guidance.txt').read_text())
                c.ingest('gguf',transcript(good.replace('Run the tests','Fix normalize.py and run the tests')))
                self.assertEqual(json.loads((tmp/'out/gguf/audit.json').read_text())['status'],'N/E: contaminated (DEV-specific strings)')
                self.assertFalse((tmp/'out/gguf/frozen-guidance.txt').exists())
                c.ingest('gguf',transcript('<<<ANSWER>>>\nnothing\n<<<END ANSWER>>>'))
                self.assertEqual(json.loads((tmp/'out/gguf/audit.json').read_text())['status'],'N/E: no edits')
            finally:c.OUT=pathlib.Path(c.ROOT/'harness2/h2claude')
            print('\ncall',meta['call'],'files',sorted(str(p.relative_to(cap)) for p in cap.rglob('*') if p.is_file())[:12],'mission chars',len((cap/'MISSION.md').read_text()))

if __name__=='__main__':unittest.main()
