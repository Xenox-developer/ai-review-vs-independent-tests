"""Produce only case-scoped worker inputs. No oracle or references in execution/."""
import hashlib
import json
from pathlib import Path
import random
import shutil

from .dataset import export

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261109


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False) + '\n')


COMMON = '''Work only in this isolated synthetic task. No network or packages.
Read spec.md and public.json. Use the required output format. Do not change the
specification, public tests or checker. No access to other tasks or any reference
implementation is required. Make the requested artifact, then call
invariant_validate once your work is ready. A passing validation freezes the
candidate; finish without additional writes. Passing public tests is not proof
of full correctness. Your time budget is bounded; prioritize the contract.
'''


def prompt(phase, arm=''):
    if phase == 'initial':
        return COMMON + 'Implement the complete contract in solution.py, replacing the incomplete starter. Export solve(data).\n'
    if phase == 'feedback' and arm == 'review':
        return COMMON + '''Review solution.py for correctness against the complete specification.
Do not modify solution.py. Write ONLY feedback.json with this exact structure:
{"assessment":"likely_correct" or "needs_changes","issues":["specific defect and counterexample", ...]}.
Use an empty issues list if no defect is found. You may inspect/run the candidate.
Do not invent defects; report concrete reproducible problems, not style comments.
'''
    if phase == 'feedback':
        return COMMON + '''Independently construct behavioral tests from the specification and ORIGINAL starter.
You have NOT been given the candidate implementation. Do not implement the task
or change solution.py. Write ONLY feedback.json:
{"tests":[{"input":<JSON>,"expect":<exact JSON output>},
          {"input":<JSON>,"error":"ValueError"}]}.
Use 1..32 tests. Each has input and exactly one of expect/error. Include boundary,
regression and specification cases with independently calculated expected values.
Do not import a model-written solution to calculate expected answers.
'''
    return COMMON + '''Repair solution.py against the complete specification using feedback.json.
Only solution.py is an accepted implementation output. Review feedback may be
mistaken; independently assess it. In the tests arm feedback contains qualified
tests and their execution against the initial candidate, plus rejected-test
counts. Qualified tests passed an independent correct reference and are frozen.
Run focused checks if useful; do not edit any frozen feedback/test inputs.
If the candidate is correct, preserve it. Do not weaken checks to obtain green.
'''


def order(phase):
    ids = [t['id'] for t in export()]
    rng = random.Random(SEED)
    rng.shuffle(ids)
    if phase == 'initial': return [(x,'') for x in ids]
    result = []
    for name in ids:
        arms = ['review','tests']; rng.shuffle(arms)
        result.extend((name, arm) for arm in arms)
    return result


def build(phase, initial=None, feedback=None):
    project = ROOT/'execution'/phase
    if project.exists():
        raise FileExistsError(f'Refusing to replace stage: {project}')
    project.mkdir(parents=True)
    shutil.copyfile(ROOT/'lab/check.py',project/'check.py')
    cases = []
    by_id = {x['id']:x for x in export()}
    for name, arm in order(phase):
        task = by_id[name]
        key = name + ('--'+arm if arm else '')
        folder = project/'inputs'/key; folder.mkdir(parents=True)
        source = task['starter'] if phase == 'initial' or (phase == 'feedback' and arm == 'tests') else initial[name]
        (folder/'solution.py').write_text(source)
        (folder/'spec.md').write_text(task['spec']+'\n')
        dump(folder/'public.json',task['public'])
        (folder/'prompt.md').write_text(prompt(phase,arm))
        data = {'phase':phase,'arm':arm,'public':task['public']}
        fixture_names = ['solution.py','spec.md','public.json']
        if phase == 'repair':
            value = feedback[key]
            dump(folder/'feedback.json',value)
            fixture_names += ['feedback.json']
            if arm == 'tests': data['qualified'] = value['tests']
        dump(folder/'case.json',data)
        cases.append({'id':key,'prompt_file':f'inputs/{key}/prompt.md',
                      'input_file':f'inputs/{key}/case.json',
                      'fixtures':[{'source':f'inputs/{key}/{p}','destination':p} for p in fixture_names]})
    recipe = {'schema_version':1,'name':f'code-verification-{phase}',
              'runner':{'type':'codex','completion':'validated'},
              'workspace':{'include':['check.py'],'exclude':[]},
              'variants':[{'id':'medium','effort':'medium'}],
              'cases':cases,'repetitions':1,
              'execution':{'max_parallel':1,'trial_cpus':2,'trial_memory_mib':2048,'trial_timeout_seconds':180},
              'evaluator':{'argv':['python3','-B','check.py'],'source_paths':['check.py'],'timeout_seconds':15},
              'artifacts':['solution.py','feedback.json'],'external_dependencies':[],'secret_refs':{}}
    dump(project/'experiment.json',recipe)
    return project


def freeze():
    manifest = ROOT/'evidence/frozen.json'
    if manifest.exists(): raise FileExistsError('Protocol already frozen')
    dump(ROOT/'evidence/tasks.json',export())
    files = ['PROTOCOL.md','lab/dataset.py','lab/check.py','lab/prepare.py','lab/run.py','lab/runtime.json',
             'lab/report.py','tests/test_protocol.py','evidence/tasks.json']
    value = {'schema_version':1,'seed':SEED,'planned_sessions':40,'max_seconds':None,
             'files':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
    dump(manifest,value)
    return value


if __name__ == '__main__':
    freeze()
    print(build('initial'))
