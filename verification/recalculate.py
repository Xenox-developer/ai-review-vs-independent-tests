"""Independent portable scorer for a public clone. No INVARIANT or model calls.

--image must name an already-local Python 3.12 image with IANA tzdata. The
original host uses the immutable image in lab/runtime.json. A different image
is explicitly reported and must not be described as an identical environment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def evaluate(image, source, examples):
    with tempfile.TemporaryDirectory(prefix='recalculate-') as d:
        directory=Path(d)
        (directory/'solution.py').write_text(source)
        (directory/'examples.json').write_text(json.dumps(examples))
        (directory/'score.py').write_text('''from pathlib import Path
import json
import unittest
namespace={}
exec(compile(Path('/data/solution.py').read_text(),'/data/solution.py','exec'),namespace)
cases=json.loads(Path('/data/examples.json').read_text())
assertions=unittest.TestCase()
passes=[]
for case in cases:
    argument=json.loads(json.dumps(case['input']))
    original=json.dumps(argument,sort_keys=True)
    try:
        if 'error' in case:
            with assertions.assertRaises(ValueError):
                namespace['solve'](argument)
        else:
            answer=namespace['solve'](argument)
            assertions.assertEqual(json.dumps(answer,sort_keys=True),json.dumps(case['expect'],sort_keys=True))
        assertions.assertEqual(json.dumps(argument,sort_keys=True),original)
        passes.append(True)
    except Exception:
        passes.append(False)
print(json.dumps({'passed':all(passes),'checks':len(cases)}))
''')
        command=['docker','run','--rm','--pull=never','--network','none','--read-only','--cpus','1',
                 '--memory','256m','--pids-limit','32','--cap-drop','ALL','--security-opt','no-new-privileges',
                 '--mount',f'type=bind,source={directory},target=/data,readonly',image,
                 'python3','-B','/data/score.py']
        proc=subprocess.run(command,capture_output=True,text=True,timeout=15)
        if proc.returncode: raise RuntimeError(proc.stderr)
        return json.loads(proc.stdout)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--image',help='Already-local Python 3.12 image, no automatic pull')
    args=parser.parse_args()
    frozen=json.loads((ROOT/'evidence/frozen.json').read_text())
    for name,wanted in frozen['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==wanted,name
    original=json.loads((ROOT/'lab/runtime.json').read_text())['oracle_image']
    image=args.image or original
    subprocess.run(['docker','image','inspect',image],check=True,capture_output=True,timeout=15)
    tasks=json.loads((ROOT/'evidence/tasks.json').read_text())
    saved=json.loads((ROOT/'results/scores.json').read_text())
    counts={name:0 for name in ('initial','review','tests')}
    differences=[]
    for task in tasks:
        name=task['id']
        for condition in counts:
            phase='initial' if condition=='initial' else 'repair'
            case=name if condition=='initial' else name+'--'+condition
            folder=ROOT/'evidence/artifacts'/phase/case
            source=(folder/'solution.py').read_text()
            diff=json.loads((folder/'diff.json').read_text())
            expected=next(r['after']['sha256'] for r in diff['changes'] if r['path']=='solution.py')
            assert hashlib.sha256(source.encode()).hexdigest()==expected
            result=evaluate(image,source,task['public']+task['hidden'])
            recorded=next(r[condition] for r in saved['tasks'] if r['task']==name)
            if result['passed']!=recorded['passed']:
                differences.append({'task':name,'condition':condition,'primary_passed':recorded['passed'],
                                    'independent_assertRaises_passed':result['passed']})
            counts[condition]+=result['passed']
    print(json.dumps({'passed':not differences,'image':image,'same_image_as_original':image==original,
                      'tasks':len(tasks),'source_snapshots':3*len(tasks),'counts':counts,
                      'primary_counts':{k:saved['summary'][k]['passed'] for k in counts},
                      'differences':differences,
                      'exception_semantics':'assertRaises(ValueError) accepts subclasses; frozen primary matches exact class name'},indent=2))
    if differences: sys.exit(1)


if __name__=='__main__':main()
