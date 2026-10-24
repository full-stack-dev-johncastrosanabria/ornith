"""Infrastructure check: resume retains failures instead of retrying until green."""
import json,pathlib,tempfile,unittest
from unittest.mock import patch
import campaign
import memory
from types import SimpleNamespace

class ResumeTests(unittest.TestCase):
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

if __name__=='__main__':unittest.main()
