import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lab.check import feedback_valid, run_examples
from lab.dataset import export
from lab.prepare import order
from lab import prepare
from lab.run import new_file


class ProtocolTests(unittest.TestCase):
    def test_test_authors_receive_originals_without_candidates_or_oracles(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'lab').mkdir()
            (root/'lab/check.py').write_text((prepare.ROOT/'lab/check.py').read_text())
            with patch.object(prepare,'ROOT',root):
                project=prepare.build('feedback',initial={t['id']:'CANDIDATE_MARKER\n' for t in export()})
            recipe=json.loads((project/'experiment.json').read_text())
            self.assertEqual(recipe['workspace']['include'],['check.py'])
            for task in export():
                stem=project/'inputs'
                self.assertEqual((stem/(task['id']+'--tests')/'solution.py').read_text(),task['starter'])
                self.assertEqual((stem/(task['id']+'--review')/'solution.py').read_text(),'CANDIDATE_MARKER\n')
                self.assertNotIn('hidden',json.loads((stem/(task['id']+'--tests')/'case.json').read_text()))
            self.assertFalse(any(p.name in ('dataset.py','tasks.json') for p in project.rglob('*')))

    def test_oracle_accepts_references_and_rejects_originals(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d)/'candidate.py'
            for task in export():
                with self.subTest(task=task['id']):
                    source.write_text(task['reference'])
                    rows = run_examples(source,task['public']+task['hidden'])
                    self.assertTrue(all(r['passed'] for r in rows),rows)
                    source.write_text(task['starter'])
                    self.assertTrue(all(r['passed'] for r in run_examples(source,task['public'])))
                    self.assertTrue(any(not r['passed'] for r in run_examples(source,task['hidden'])))

    def test_nonmutation_is_an_independent_requirement(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.py';p.write_text('def solve(d):\n d.clear()\n return 1\n')
            self.assertFalse(run_examples(p,[{'input':{'x':1},'expect':1}])[0]['passed'])

    def test_branch_order_is_paired_balanced_and_reproducible(self):
        self.assertEqual(order('feedback'),order('repair'))
        rows=order('feedback')
        self.assertEqual(len(rows),16)
        first_arms=[]
        for i in range(0,16,2):
            self.assertEqual(rows[i][0],rows[i+1][0])
            self.assertEqual({rows[i][1],rows[i+1][1]},{'review','tests'})
            first_arms.append(rows[i][1])
        self.assertGreater(len(set(first_arms)),1)

    def test_feedback_schema_does_not_accept_empty_test_coverage(self):
        self.assertFalse(feedback_valid({'tests':[]},'tests'))
        self.assertFalse(feedback_valid({'tests':[{'input':{},'expect':1,'error':'ValueError'}]},'tests'))
        self.assertTrue(feedback_valid({'assessment':'likely_correct','issues':[]},'review'))

    def test_added_artifact_reconstruction_preserves_source(self):
        text='def solve(x):\n    return x\n'
        diff={'changes':[{'path':'solution.py','before':None,'after':{'sha256':hashlib.sha256(text.encode()).hexdigest()},'text_diff_truncated':False,
                         'text_diff':'--- before/solution.py\n+++ after/solution.py\n@@ -0,0 +1,2 @@\n+def solve(x):\n+    return x\n'}]}
        self.assertEqual(new_file(diff,'solution.py'),text)
        diff['changes'][0]['text_diff_truncated']=True
        with self.assertRaises(RuntimeError): new_file(diff,'solution.py')


if __name__ == '__main__': unittest.main()
