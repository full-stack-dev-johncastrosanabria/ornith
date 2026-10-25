"""Infrastructure check: resume retains failures instead of retrying until green."""
import json,pathlib,tempfile,unittest
from unittest.mock import patch
import campaign
import memory
import report
from types import SimpleNamespace

class ResumeTests(unittest.TestCase):
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

if __name__=='__main__':unittest.main()
