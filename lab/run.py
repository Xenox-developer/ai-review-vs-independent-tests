"""Execute three frozen native INVARIANT studies; never replay model attempts.

Run only under the user's standing zero-extra-spend authorization. Stdlib only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from .check import feedback_valid, run_examples
from .dataset import export
from .prepare import ROOT, build, dump


def cli(project, *args, timeout=120):
    proc = subprocess.run(['invariant',*args,'--json'],cwd=project,text=True,
                          capture_output=True,timeout=timeout)
    try: result = json.loads(proc.stdout)
    except ValueError: raise RuntimeError(f'Invalid INVARIANT response: {proc.stderr[-1000:]}')
    if proc.returncode or result.get('ok') is False:
        raise RuntimeError(json.dumps(result))
    return result.get('data',result)


def verify_freeze():
    frozen = json.loads((ROOT/'evidence/frozen.json').read_text())
    for name, digest in frozen['files'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f'Frozen input changed: {name}')
    return frozen


def initialize(project):
    cli(project,'init')
    # Local project settings only. No host access, network, downloads or installs.
    for key,value in [('command_network','none'),('resource_mode','manual'),
                      ('limits.cpus','2'),('limits.memory_mib','2048'),
                      ('limits.processes','256'),('limits.file_descriptors','1024'),
                      ('limits.scratch_mib','256'),('duration_seconds','180')]:
        cli(project,'config','set',key,value)
    receipt = cli(project,'experiment','validate','experiment.json')
    dump(ROOT/'evidence'/f'{project.name}-definition-validation.json',receipt)


def sanitized_trial(row):
    runner = row.get('runner',{})
    native = runner.get('native') or {}
    safe = {k:row.get(k) for k in ['trial_id','attempt_id','case_id','state','reason',
            'passed','evaluation','duration_seconds','usage_unavailable_reason']}
    safe['runner'] = {k:runner.get(k) for k in ['status','reason','exit_code','started_at',
                        'duration_seconds','token_usage','cleanup_confirmed']}
    safe['runner']['native'] = {k:native.get(k) for k in ['model','effort','requested_model',
                                 'requested_effort','cli_version','thread_id','turn_id']}
    safe['runner']['inference_usage'] = {k:v for k,v in (runner.get('inference_usage') or {}).items() if k != 'path'}
    if row.get('capture'): safe['candidate_digest'] = row['capture'].get('content_digest')
    if row.get('checkpoint'): safe['image'] = row['checkpoint'].get('image')
    return safe


def new_file(diff, name):
    for change in diff.get('changes',[]):
        if change['path'] != name: continue
        if change.get('before') is not None or change.get('text_diff_truncated'):
            raise RuntimeError('Expected complete added artifact; no lossy patch reconstruction')
        text = change.get('text_diff')
        if text is None: return None
        content = ''.join(line[1:] for line in text.splitlines(True)[2:] if line.startswith('+'))
        if hashlib.sha256(content.encode()).hexdigest() != change['after']['sha256']:
            raise RuntimeError('Extracted source does not match the saved snapshot digest')
        return content
    return None


def run_stage(project):
    phase = project.name
    created = cli(project,'experiment','run','experiment.json','--request-id',f'{phase}-freeze-v1','--create-only')
    study = created['id']
    dump(ROOT/'evidence'/f'{phase}-submission.json',created)
    print(json.dumps({'stage':phase,'study_id':study}),flush=True)
    command = ['invariant','experiment','execute',study,'--request-id',f'{phase}-execute-v1','--wait','--json']
    proc = subprocess.run(command,cwd=project,text=True,capture_output=True)
    # Do not infer success from CLI exit code. Fetch terminal structured evidence once.
    result = cli(project,'experiment','results',study,timeout=120)
    dump(project/'private-results.json',result)
    receipt = {k:result.get(k) for k in ['study_id','state','attempt_policy','summary','selection']}
    receipt['trials'] = [sanitized_trial(row) for row in result['trials']]
    dump(ROOT/'evidence'/f'{phase}-receipt.json',receipt)
    artifacts = {}
    for row in result['trials']:
        key = row['case_id']
        if not ((row.get('capture') or {}).get('complete') and (row.get('checkpoint') or {}).get('complete')):
            artifacts[key] = {'source':None,'feedback':None,'terminal':False}; continue
        diff = cli(project,'experiment','diff',row['attempt_id'])
        folder = ROOT/'evidence/artifacts'/phase/key
        folder.mkdir(parents=True,exist_ok=True)
        dump(folder/'diff.json',diff)
        source,feedback = new_file(diff,'solution.py'),new_file(diff,'feedback.json')
        if source is not None: (folder/'solution.py').write_text(source)
        if feedback is not None: (folder/'feedback.json').write_text(feedback)
        artifacts[key] = {'source':source,'feedback':feedback,'terminal':row['state'] == 'succeeded' and row['runner'].get('status') == 'completed'}
    return artifacts,receipt


def isolated_examples(source, examples):
    """No model process is present; evaluate in a fresh offline, read-only container."""
    with tempfile.TemporaryDirectory(prefix='heldout-') as directory:
        folder = Path(directory)
        (folder/'solution.py').write_text(source)
        dump(folder/'examples.json',examples)
        shutil.copyfile(ROOT/'lab/check.py',folder/'check.py')
        (folder/'evaluate.py').write_text("import json\nfrom pathlib import Path\nfrom check import run_examples\nprint(json.dumps(run_examples(Path('/data/solution.py'),json.loads(Path('/data/examples.json').read_text()))))\n")
        command = ['docker','run','--rm','--network','none','--read-only','--cpus','1',
                   '--memory','256m','--pids-limit','32','--cap-drop','ALL','--security-opt','no-new-privileges',
                   '--mount',f'type=bind,source={folder},target=/data,readonly',
                   '--tmpfs','/tmp:rw,noexec,nosuid,size=16m',json.loads((ROOT/'lab/runtime.json').read_text())['oracle_image'],
                   'python3','-B','/data/evaluate.py']
        try:
            result = subprocess.run(command,capture_output=True,text=True,timeout=15)
            if result.returncode: return {'available':False,'error':'evaluation_process_error','detail':result.stderr[-500:]}
            rows = json.loads(result.stdout)
            return {'available':True,'passed':all(x['passed'] for x in rows),'checks':rows}
        except (subprocess.TimeoutExpired,ValueError):
            return {'available':False,'error':'evaluation_timeout_or_invalid_output'}


def qualify(feedback, initials):
    repair_feedback = {}; details = {}
    for task in export():
        name = task['id']
        for arm in ('review','tests'):
            key = name+'--'+arm
            raw = feedback[key]
            try: value = json.loads(raw['feedback'])
            except (ValueError,TypeError): value = None
            valid = raw['terminal'] and feedback_valid(value,arm)
            if arm == 'review':
                repair_feedback[key] = value if valid else {'assessment':'unavailable','issues':[],'error':'missing_or_invalid_review'}
                details[key] = {'valid':valid, 'feedback':value}
                continue
            tests = value['tests'] if valid else []
            reference = isolated_examples(task['reference'],tests) if tests else {'available':True,'checks':[]}
            if not reference['available']: raise RuntimeError('Reference qualification failed to execute; no silent test rejection')
            qualified = [t for t,row in zip(tests,reference['checks']) if row['passed']]
            # Only AFTER reference qualification, execute frozen qualified tests on candidate.
            candidate = isolated_examples(initials[name],qualified) if qualified else None
            repair_feedback[key] = {'tests':qualified,'submitted':len(tests),'rejected':len(tests)-len(qualified),
                                    'format_valid':valid,'initial_candidate_execution':candidate}
            details[key] = {'valid':valid,'submitted':tests,'reference_execution':reference,
                            'qualified':qualified,'initial_candidate_execution':candidate}
    dump(ROOT/'evidence/qualification.json',details)
    return repair_feedback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true',help='Consume the currently authorized Codex subscription for the frozen 40-session design')
    args = parser.parse_args()
    if not args.execute: parser.error('Use --execute to start real model sessions')
    verify_freeze()
    state = ROOT/'evidence/execution.json'
    if state.exists(): raise RuntimeError('A run already exists. Inspect/recover its saved study IDs; never replay uncertain model work.')
    initial_project = ROOT/'execution/initial'
    initialize(initial_project)
    started = time.time()
    metadata = {'status':'running','started_at':started,'planned_sessions':40,'global_wall_limit':None,
                'authorization':'User removed artificial generation and overall duration caps on 2026-11-09; zero additional spending remains in force.',
                'invariant_version':subprocess.check_output(['invariant','--version'],text=True).strip(),
                'tested_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
    dump(state,metadata)
    try:
        initial,first = run_stage(initial_project)
        if not all(row['terminal'] and row['source'] is not None for row in initial.values()):
            raise RuntimeError('Initial stage incomplete: both treatments would lack matched starting candidates')
        sources = {name:row['source'] for name,row in initial.items()}
        project = build('feedback',initial=sources); initialize(project)
        feedback,second = run_stage(project)
        prepared = qualify(feedback,sources)
        project = build('repair',initial=sources,feedback=prepared); initialize(project)
        repairs,third = run_stage(project)
        if not all(row['terminal'] and row['source'] is not None for row in repairs.values()):
            raise RuntimeError('Repair stage incomplete; preserve outcomes without claiming completed comparison')
        metadata['status'] = 'completed'
    except Exception as error:
        metadata.update(status='incomplete',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        metadata.update(finished_at=time.time(),wall_seconds=time.time()-started)
        dump(state,metadata)
    from .report import report
    report()


if __name__ == '__main__': main()
