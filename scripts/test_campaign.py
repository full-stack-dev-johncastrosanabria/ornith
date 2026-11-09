"""Infrastructure check: resume retains failures instead of retrying until green."""
import json,pathlib,tempfile,unittest
from unittest.mock import patch
import campaign
import memory
import report
import server
from types import SimpleNamespace

class ResumeTests(unittest.TestCase):
    def test_first_tool_latency_uses_earliest_start_not_completion_order(self):
        events=[{'type':'tool_use','timestamp':3000,'part':{'state':{'time':{'start':2100}}}},{'type':'tool_use','timestamp':4000,'part':{'state':{'time':{'start':1900}}}}]
        self.assertEqual(report.execution_stats({'agent':{'events':events,'started_epoch_ms':1000},'first_tool_from_launch_s':2})['first_tool_from_launch_s'],0.9)
        self.assertIsNone(report.first_tool_latency([{'type':'tool_use','timestamp':3000}],1000))
        self.assertIsNone(report.first_tool_latency(events,5000))
    def test_source_executor_failure_does_not_replace_global_tool_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            results=pathlib.Path(directory)
            (results/'smoke-agent-mlx-20261024T100000.json').write_text(json.dumps({'passed':3,'rows':[{'agent':{}}]}))
            (results/'smoke-agent-mlx-20261024T230000.json').write_text(json.dumps({'passed':0,'rows':[{'agent':{'executor':'official-pinned-opencode-source'}}]}))
            with patch.object(report,'RESULTS',results):
                self.assertEqual(report.latest('smoke-agent-mlx-*.json',executor='global')['passed'],3)
                self.assertEqual(report.latest('smoke-agent-mlx-*.json')['passed'],0)
    def test_stop_waits_for_process_after_port_closes(self):
        with tempfile.TemporaryDirectory() as directory:
            state=pathlib.Path(directory)/'server.json';lock=pathlib.Path(directory)/'lock';lock.touch()
            state.write_text(json.dumps({'pid':123456,'port':8085,'cmd':['/mock/llama-server']}))
            replies=[SimpleNamespace(stdout='/mock/llama-server'),SimpleNamespace(stdout='S'),SimpleNamespace(stdout='')]
            with patch.object(server,'STATE',state),patch.object(server,'LOCK',lock),patch.object(server.subprocess,'run',side_effect=replies),patch.object(server.os,'killpg'),patch.object(server.os,'waitpid',return_value=(0,0)),patch.object(server.socket,'socket') as sock,patch.object(server.time,'sleep') as sleep:
                sock.return_value.__enter__.return_value.connect_ex.return_value=1
                server.stop()
            self.assertEqual(sleep.call_count,1)
            self.assertFalse(state.exists());self.assertFalse(lock.exists())
    def test_stop_accepts_an_exited_zombie_of_another_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            state=pathlib.Path(directory)/'server.json';lock=pathlib.Path(directory)/'lock';lock.touch()
            state.write_text(json.dumps({'pid':123456,'port':8085,'cmd':['/mock/llama-server']}))
            replies=[SimpleNamespace(stdout='/mock/llama-server'),SimpleNamespace(stdout='Z')]
            with patch.object(server,'STATE',state),patch.object(server,'LOCK',lock),patch.object(server.subprocess,'run',side_effect=replies),patch.object(server.os,'killpg'),patch.object(server.os,'waitpid',side_effect=ChildProcessError),patch.object(server.socket,'socket') as sock,patch.object(server.time,'sleep') as sleep:
                sock.return_value.__enter__.return_value.connect_ex.return_value=1
                server.stop()
            self.assertEqual(sleep.call_count,0);self.assertFalse(state.exists())
    def test_failed_timeout_restart_keeps_the_measured_row(self):
        import bench_tasks
        timed_out={'events':[{'type':'step_finish','part':{}}],'timeout':True,'wall_s':1200}
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);fixture=root/'benchmarks/fixtures/F7-B';(fixture/'tests').mkdir(parents=True);(fixture/'TASK.md').write_text('task')
            (root/'benchmarks/fixtures/manifest.json').write_text(json.dumps({'tasks':[{'task':'F7-B','command':'true'}]}))
            with patch.object(bench_tasks,'ROOT',root),patch.object(bench_tasks,'grade',return_value={'rc':1}),patch.object(bench_tasks,'snapshot',return_value={}),patch.object(bench_tasks,'run',return_value=timed_out),patch.object(server,'stop',side_effect=RuntimeError('zombie')):
                row=bench_tasks.task('F7-B',{'kind':'mlx','model_id':'m'},label='t')
        self.assertEqual((row['status'],row['timeout_recovery']['server_restarted']),('fail',False))
    def test_infrastructure_interruptions_remain_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);results=root/'benchmarks/results';results.mkdir(parents=True)
            (results/'tasks-mlx-control-20261024.json').write_text(json.dumps({'rows':[{'task':'F7-A','status':'fail'},{'task':'F7-B','status':'infrastructure','resource_abort':['disk below reserve']}]}))
            with patch.object(campaign,'ROOT',root):found=campaign.existing_tasks('mlx','control')
            self.assertEqual(list(found),['F7-A'])
    def test_negative_measurements_are_completed_attempts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);results=root/'benchmarks/results';results.mkdir(parents=True)
            (results/'tasks-mlx-control-20261024.json').write_text(json.dumps({'rows':[{'task':'F7-A','status':'fail'},{'task':'F7-B','status':'pass'}]}))
            with patch.object(campaign,'ROOT',root):
                found=campaign.existing_tasks('mlx','control')
            self.assertEqual(found['F7-A']['status'],'fail')
            self.assertEqual([t for t in ['F7-A','F7-B','F7-C','F7-D'] if t not in found],['F7-C','F7-D'])
    def test_disk_reserve_stops_before_more_inference(self):
        with patch.object(memory.shutil,'disk_usage',return_value=SimpleNamespace(free=memory.RESERVE-1)):
            with self.assertRaises(SystemExit) as error:memory.require_space()
            self.assertEqual(error.exception.code,75)
        with patch.object(memory.shutil,'disk_usage',return_value=SimpleNamespace(free=memory.RESERVE)):
            memory.require_space()
    def test_report_does_not_fill_new_cohort_with_old_results(self):
        with tempfile.TemporaryDirectory() as directory:
            results=pathlib.Path(directory)
            (results/'tasks-mlx-control-20261024T100000.json').write_text(json.dumps({'label':'control','rows':[{'task':'F7-A','status':'fail'},{'task':'F7-B','status':'fail'}]}))
            (results/'tasks-mlx-control-cleared-host-20261024T160000.json').write_text(json.dumps({'label':'control-cleared-host','rows':[{'task':'F7-A','status':'fail'}]}))
            with patch.object(report,'RESULTS',results):rows=report.group('mlx','control')
            self.assertEqual([r['task'] for r in rows],['F7-A'])
    def test_correct_timed_out_artifact_is_not_a_failed_quality_score(self):
        rows=[{'status':'fail','acceptance':{'rc':0},'tests_unchanged':True}]
        self.assertEqual(report.artifact_quality(rows),'1/1')
        self.assertEqual(report.quality(rows),'0/1 scored')
    def test_report_excludes_infrastructure_from_quality_denominators(self):
        rows=[{'status':'fail','acceptance':{'rc':1},'tests_unchanged':True},{'status':'infrastructure','acceptance':{'rc':1},'tests_unchanged':True}]
        self.assertEqual(report.artifact_quality(rows),'0/1')
        self.assertEqual(report.quality(rows),'0/1 scored; 1 infrastructure')
    def test_rank_is_quality_first_and_flags_close_top_two(self):
        import score_models
        s=lambda k,p,t,d:{'kind':k,'complete':True,'passes':p,'total_s':t,'decode_tps':d}
        ranked,provisional=score_models.rank([s('fast',3,900,15),s('slow',4,2400,4.6),{'kind':'ne','complete':False}])
        self.assertEqual([r['kind'] for r in ranked],['slow','fast']);self.assertTrue(provisional)
        ranked,provisional=score_models.rank([s('a',2,900,15),s('b',4,2400,4.6)]);self.assertFalse(provisional)
        self.assertEqual([r['kind'] for r in score_models.rank([s('a',3,900,9),s('b',3,800,5)])[0]],['b','a'])
    def test_evict_removes_only_the_candidate_cache_repo(self):
        import campaign_models
        with tempfile.TemporaryDirectory() as directory:
            home=pathlib.Path(directory);hub=home/'.cache/huggingface/hub'
            snap=hub/'models--org--cand/snapshots/rev';snap.mkdir(parents=True);keep=hub/'models--org--other';keep.mkdir()
            models=home/'lab/models';models.mkdir(parents=True);(models/'qwen3.5-9b-mlx').symlink_to(snap,target_is_directory=True)
            with patch.object(campaign_models,'ROOT',home/'lab'),patch.object(pathlib.Path,'home',return_value=home):campaign_models.evict('qwen')
            self.assertFalse((hub/'models--org--cand').exists());self.assertTrue(keep.exists());self.assertFalse((models/'qwen3.5-9b-mlx').is_symlink())
            (models/'qwen3.5-9b-mlx').symlink_to(home,target_is_directory=True)
            with patch.object(campaign_models,'ROOT',home/'lab'),self.assertRaises(StopIteration):campaign_models.evict('qwen')
    def test_evict_frees_shared_blobs_but_keeps_ones_other_repos_use(self):
        import campaign_models
        with tempfile.TemporaryDirectory() as directory:
            home=pathlib.Path(directory);hub=home/'.cache/huggingface/hub';store=hub/'blobs/ab';store.mkdir(parents=True)
            own=store/'own';own.write_text('w');common=store/'common';common.write_text('c')
            for repo,names in (('models--org--cand',('own','common')),('models--org--other',('common',))):
                snap=hub/repo/'snapshots/rev';snap.mkdir(parents=True);(hub/repo/'blobs').mkdir()
                for n in names:(hub/repo/'blobs'/n).symlink_to(f'../../blobs/ab/{n}');(snap/f'{n}.gguf').symlink_to(f'../../blobs/{n}')
            models=home/'lab/models';models.mkdir(parents=True);(models/'sera-8b.gguf').symlink_to(hub/'models--org--cand/snapshots/rev/own.gguf')
            with patch.object(campaign_models,'ROOT',home/'lab'),patch.object(pathlib.Path,'home',return_value=home):campaign_models.evict('sera8')
            self.assertEqual((own.exists(),common.exists(),(hub/'models--org--cand').exists(),(hub/'models--org--other').exists()),(False,True,False,True))
            self.assertFalse((models/'sera-8b.gguf').is_symlink())

    def test_every_candidate_is_wired_end_to_end(self):
        import campaign_models,opencode_local,score_models
        for kind in score_models.KINDS:
            self.assertIn(kind,server.PORTS);self.assertIn(kind,score_models.NAMES)
            self.assertTrue(opencode_local.configuration(kind,'m')[1].endswith('/local'))
            if kind in campaign_models.FETCH:self.assertIn(kind,campaign_models.LINKS);self.assertIn(kind,campaign_models.EVICT|campaign_models.KEEP)
        self.assertEqual(len(set(server.PORTS.values())),len(server.PORTS))

    def test_reasoning_arm_is_mechanical(self):
        import campaign_models as c
        capped={'type':'step_finish','part':{'reason':'length','tokens':{'output':4096}}}
        full=lambda ev:{t:{'agent':{'events':ev}} for t in c.TASKS}
        self.assertEqual(c.reasoning_arm('gemma',full([])),'on')
        self.assertEqual(c.reasoning_arm('mlx',full([capped])),'off')
        self.assertIsNone(c.reasoning_arm('mlx',full([])))
        self.assertIsNone(c.reasoning_arm('gemma',{'F7-A':{'agent':{'events':[]}}}))
    def test_vendor_sampling_only_applies_to_its_arm_and_kind(self):
        import opencode_local
        agent=lambda k:opencode_local.configuration(k,'m')[0]['agent']['ornith-code']
        self.assertEqual(agent('gemma')['temperature'],.6)
        with patch.dict(opencode_local.os.environ,{'LAB_SAMPLING':'vendor'}):
            self.assertEqual((agent('gemma')['temperature'],agent('gemma')['top_p']),(1.0,.95))
            self.assertEqual(agent('mlx')['temperature'],.6)

    def test_lab_profile_reaches_the_opencode_limits(self):
        import opencode_local
        limit=lambda:opencode_local.configuration('gguf','m')[0]['provider']['ornith-gguf']['models']['local']['limit']
        self.assertEqual(limit(),{'context':16384,'output':4096})
        with patch.dict(opencode_local.os.environ,{'LAB_PROFILE':'runtimes/profile-cap8k.json'}):self.assertEqual(limit(),{'context':24576,'output':8192})

    def test_cloud_editor_parse_whitelist_and_scan(self):
        import cloud_editor_arm as c
        out="<<<EDIT context/harness/systemprompt.md>>>\nA\nB\n<<<END EDIT>>>\n<<<EDIT context/harness/scripts/x.py>>>\nz\n<<<END EDIT>>>\n<<<ANSWER>>>\nok\n<<<END ANSWER>>>"
        edits,answers,outside,bad=c.parse(out)
        self.assertEqual((edits['systemprompt.md'],answers,outside,bad),('A\nB',['ok'],'',['scripts/x.py']))
        self.assertTrue(c.scan("call normalize(x) on ['a', 'b']")[0]);self.assertEqual(c.scan('Normalize paths first'),({},1))

class RouterTests(unittest.TestCase):
    def test_router_never_touches_a_live_foreign_server_but_clears_stale_state(self):
        import model_router as m
        calls=[];m.mine[0]=None;m.busy[0]=1
        states=iter([{'kind':'gguf','pid':1,'port':8083},{'kind':'bonsai','pid':2,'port':8085}])
        with patch.object(m,'state',lambda:next(states)),patch.object(m,'alive',lambda pid:True):
            with self.assertRaises(RuntimeError):m.ensure('bonsai')
        states=iter([{'kind':'gguf','pid':1,'port':8083},{'kind':'bonsai','pid':2,'port':8085}])
        with patch.object(m,'state',lambda:next(states)),patch.object(m,'alive',lambda pid:False),\
             patch.object(m,'stop',lambda:calls.append('stop')),patch.object(m,'start',lambda k:calls.append(k)):
            self.assertEqual(m.ensure('bonsai')['pid'],2)
        self.assertEqual(calls,['stop','bonsai']);self.assertEqual(m.mine[0],2)
        m.busy[0]=2  # the loaded model is still streaming another request: do not swap under it
        with patch.object(m,'state',lambda:{'kind':'bonsai','pid':2,'port':8085}):
            with self.assertRaises(RuntimeError):m.ensure('gguf')
        m.busy[0]=0;m.mine[0]=None

if __name__=='__main__':unittest.main()
