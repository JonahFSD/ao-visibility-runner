import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runner

class RunnerTests(unittest.TestCase):
    def test_entity(self):
        self.assertFalse(runner.score('The ocean is blue', [])['brand_mention_heuristic'])
        self.assertTrue(runner.score("Athlete’s Ocean", [])['brand_mention_heuristic'])
        self.assertTrue(runner.score('Athletes Ocean', [])['brand_mention_heuristic'])
    def test_citation_domains(self):
        score = runner.score('', ['https://app.athletesocean.com/a', 'https://athletesocean.com.evil.test'])
        self.assertEqual(len(score['owned_urls']), 1)
        self.assertEqual(len(score['third_party_urls']), 1)
    def test_bad_adapter(self):
        for output in ({'answer':'', 'citations':[]}, {'answer':'a', 'citations':['javascript:alert(1)']}):
            with self.assertRaises(ValueError): runner.validate_output(output)
    def test_suite(self):
        suite = runner.load_suite(Path(runner.__file__).with_name('prompts.json'))
        self.assertEqual(len(suite['prompts']), 20)
    def test_demo_resume_and_config_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            cmd = [sys.executable, runner.__file__, 'run', '--demo', '--out', folder]
            subprocess.run(cmd, check=True, capture_output=True)
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertEqual(len(runner.records(Path(folder)/'evidence.jsonl')), 20)
            summary = runner.report(folder)
            self.assertEqual(summary['successful'], 0)
            self.assertEqual(summary['demo'], 20)
            self.assertNotEqual(subprocess.run(cmd+['--repetitions','3'], capture_output=True).returncode, 0)
    def test_live_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, runner.__file__, 'run', '--out', folder], capture_output=True)
            self.assertNotEqual(result.returncode, 0)

if __name__ == '__main__': unittest.main()
