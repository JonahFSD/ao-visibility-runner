import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class BrowserCourierTests(unittest.TestCase):
    def test_reservation_save_resume(self):
        with tempfile.TemporaryDirectory() as d:
            def call(*args, answer=None):
                return subprocess.run([sys.executable,str(ROOT/'browser_runner.py'),*args],input=answer,text=True,capture_output=True)
            self.assertEqual(call('init',d,'--model','TEST FIXTURE','--effort','unknown','--search-mode','unknown','--settings-note','offline test only').returncode,0)
            self.assertNotEqual(call('init',d,'--model','x','--effort','x','--search-mode','x','--settings-note','x').returncode,0)
            ticket=json.loads(call('prompt',d).stdout)
            self.assertEqual(ticket['key'],'q01:1')
            citations=Path(d)/'citations.json'; citations.write_text('[]')
            args=['save',d,'--key','q01:1','--citations',str(citations),'--evidence','offline-test-fixture']
            self.assertNotEqual(call(*args,answer=ticket['prompt']).returncode,0)
            self.assertEqual(call('fail',d,'--reason','fixture error').returncode,0)
            self.assertEqual(json.loads(call('prompt',d).stdout)['key'],'q01:1')
            self.assertEqual(call(*args,answer='Offline unit test fixture answer, not an actual ChatGPT response.').returncode,0)
            self.assertNotEqual(call(*args,answer='Duplicate answer must be rejected.').returncode,0)
            self.assertEqual(json.loads(call('prompt',d).stdout)['key'],'q02:1')
            self.assertEqual(json.loads(call('status',d).stdout)['remaining'],19)
            self.assertNotEqual(call('unknown',d,'--key','q02:1').returncode,0)
            self.assertEqual(call('fail',d,'--reason','submitted answer lost').returncode,0)
            self.assertNotEqual(call('unknown',d,'--key','q03:1').returncode,0)
            self.assertEqual(call('unknown',d,'--key','q02:1').returncode,0)
            self.assertEqual(json.loads(call('prompt',d).stdout)['key'],'q03:1')
            self.assertEqual(json.loads(call('status',d).stdout),
                             {'saved':1,'unknown':1,'remaining':18,'next':'q03'})
            unknown=json.loads((Path(d)/'evidence.jsonl').read_text().splitlines()[1])
            self.assertEqual(unknown['status'],'error')
            self.assertIsNone(unknown['scores'])
if __name__=='__main__': unittest.main()
