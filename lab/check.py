"""Fixed public evaluator. It never contains the held-out oracle/reference."""
import copy
import json
import os
from pathlib import Path
import sys
import types


def run_examples(source, examples):
    module = types.ModuleType('candidate')
    exec(compile(Path(source).read_text(), str(source), 'exec'), module.__dict__)
    results = []
    for i, test in enumerate(examples):
        value = copy.deepcopy(test['input'])
        before = copy.deepcopy(value)
        try:
            actual = module.solve(value)
            # JSON equality must distinguish booleans from numbers.
            passed = 'expect' in test and json.dumps(actual, sort_keys=True) == json.dumps(test['expect'], sort_keys=True)
            detail = {'actual': actual}
        except Exception as error:
            passed = test.get('error') == type(error).__name__
            detail = {'error': type(error).__name__, 'message': str(error)[:160]}
        unchanged = json.dumps(value, sort_keys=True) == json.dumps(before, sort_keys=True)
        results.append({'index': i, 'passed': bool(passed and unchanged), 'input_unchanged': unchanged, **detail})
    return results


def valid_test(test):
    return isinstance(test, dict) and 'input' in test and ('expect' in test) != ('error' in test) and (
        'error' not in test or test['error'] == 'ValueError') and set(test) <= {'input','expect','error'}


def feedback_valid(value, mode):
    if mode == 'review':
        return isinstance(value, dict) and set(value) == {'assessment','issues'} and (
            value['assessment'] in ('likely_correct','needs_changes')) and isinstance(value['issues'],list) and (
            len(value['issues']) <= 32) and all(isinstance(x,str) and 0 < len(x) <= 2000 for x in value['issues'])
    return isinstance(value, dict) and set(value) == {'tests'} and isinstance(value['tests'],list) and (
        1 <= len(value['tests']) <= 32) and all(valid_test(x) for x in value['tests'])


def main():
    case = json.loads(Path(os.environ['INVARIANT_CASE_FILE']).read_text())
    root = Path(os.environ.get('INVARIANT_CANDIDATE_DIR') or '.')
    try:
        if case['phase'] == 'feedback':
            value = json.loads((root/'feedback.json').read_text())
            passed = feedback_valid(value,case['arm'])
            metrics = {'format_valid': int(passed)}
        else:
            rows = run_examples(root/'solution.py', case['public'] + case.get('qualified',[]))
            passed = all(x['passed'] for x in rows)
            metrics = {'checks':len(rows), 'failures':sum(not x['passed'] for x in rows)}
        print(json.dumps({'schema_version':1,'passed':passed,'metrics':metrics}))
    except Exception:
        print(json.dumps({'schema_version':1,'passed':False,'metrics':{'format_or_import_error':1}}))


if __name__ == '__main__':
    main()
