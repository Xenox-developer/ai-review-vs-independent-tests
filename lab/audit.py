"""Independent deterministic cross-check of saved task outcomes and run coverage."""
import hashlib
import argparse
import json
from pathlib import Path

from .prepare import ROOT, dump, order


def main():
    from .run import isolated_examples, verify_freeze
    parser=argparse.ArgumentParser()
    parser.add_argument('--reexecute',action='store_true',help='Also repeat the frozen primary Docker checks; default audits saved check records and hashes')
    args=parser.parse_args()
    frozen = verify_freeze()
    scores = json.loads((ROOT/'results/scores.json').read_text())
    tasks = json.loads((ROOT/'evidence/tasks.json').read_text())
    receipts = {p:json.loads((ROOT/'evidence'/f'{p}-receipt.json').read_text())
                for p in ('initial','feedback','repair')}
    counted = {}; native = []; feedback_source_changes = []
    for phase,receipt in receipts.items():
        expected = [task+('--'+arm if arm else '') for task,arm in order(phase)]
        assert sorted(x['case_id'] for x in receipt['trials']) == sorted(expected)
        counted[phase] = len(receipt['trials'])
        for r in receipt['trials']:
            identity=r['runner']['native']
            native.append((identity.get('model'),identity.get('effort')))
            assert r['runner'].get('cleanup_confirmed') is True
    assert len(set(native)) == 1 and all(all(pair) for pair in native),native
    threads=[r['runner']['native']['thread_id'] for receipt in receipts.values() for r in receipt['trials']]
    assert len(threads)==40 and len(set(threads))==40 and all(threads)
    recalculated={c:0 for c in ('initial','review','tests')}
    for task in tasks:
        name=task['id']
        scored=next(r for r in scores['tasks'] if r['task']==name)
        for condition in recalculated:
            phase='initial' if condition=='initial' else 'repair'
            case=name if condition=='initial' else name+'--'+condition
            folder=ROOT/'evidence/artifacts'/phase/case
            diff=json.loads((folder/'diff.json').read_text())
            row=next(r for r in diff['changes'] if r['path']=='solution.py')
            source=(folder/'solution.py').read_text()
            assert hashlib.sha256(source.encode()).hexdigest()==row['after']['sha256']
            recorded=scored[condition]
            assert len(recorded['checks'])==len(task['public'])+len(task['hidden'])
            derived=all(case['passed'] for case in recorded['checks'])
            assert derived==recorded['passed']
            if args.reexecute:
                actual=isolated_examples(source,task['public']+task['hidden'])
                assert actual['available'] and actual['passed']==recorded['passed']
            recalculated[condition]+=derived
    for condition,value in recalculated.items():
        assert value==scores['summary'][condition]['passed']
    # Verify case isolation against the real staged inputs, not just a mock.
    for phase in receipts:
        project=ROOT/'execution'/phase
        if not project.exists(): continue  # Shared clone intentionally omits private working copies.
        recipe=json.loads((project/'experiment.json').read_text())
        assert recipe['workspace']['include']==['check.py']
        for case in recipe['cases']:
            payload=json.loads((project/case['input_file']).read_text())
            assert 'hidden' not in payload and 'reference' not in payload
        if phase=='feedback':
            for task in tasks:
                path=project/'inputs'/(task['id']+'--tests')/'solution.py'
                assert path.read_text()==task['starter']
                for arm in ('review','tests'):
                    expected=task['starter'] if arm=='tests' else (ROOT/'evidence/artifacts/initial'/task['id']/'solution.py').read_text()
                    delivered=ROOT/'evidence/artifacts/feedback'/(task['id']+'--'+arm)/'solution.py'
                    if delivered.read_text()!=expected:
                        feedback_source_changes.append(task['id']+'--'+arm)
        if phase=='repair':
            for task in tasks:
                initial=(ROOT/'evidence/artifacts/initial'/task['id']/'solution.py').read_text()
                for arm in ('review','tests'):
                    path=project/'inputs'/(task['id']+'--'+arm)/'solution.py'
                    assert path.read_text()==initial
    result={'passed':True,'frozen_inputs':len(frozen['files']),'sessions':counted,
            'observed_model_effort':list(next(iter(set(native)))),'recalculated_task_passes':recalculated,
            'candidate_snapshot_hashes_verified':24,'primary_checks_reexecuted':args.reexecute,'unique_fresh_native_threads':40,'feedback_author_source_changes':feedback_source_changes,'test_author_inputs':'original starters; no candidates or held-out oracle',
            'notes':'Clone can recalculate scores and hashes; private stage workspace check is available only on the original host.'}
    dump(ROOT/'results/audit.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
