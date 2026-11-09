"""Recalculate all primary outcomes from saved sources without any inference."""
import json
from .prepare import ROOT, dump
from .dataset import export


def report():
    from .run import isolated_examples, verify_freeze
    verify_freeze()
    execution = json.loads((ROOT/'evidence/execution.json').read_text())
    if execution['status'] != 'completed': raise RuntimeError('Incomplete measurement; results draft forbidden')
    scores = []
    qualification = json.loads((ROOT/'evidence/qualification.json').read_text())
    for task in export():
        name = task['id']
        row = {'task':name}
        for condition in ('initial','review','tests'):
            phase = 'initial' if condition == 'initial' else 'repair'
            key = name if condition == 'initial' else name+'--'+condition
            source = (ROOT/'evidence/artifacts'/phase/key/'solution.py').read_text()
            row[condition] = isolated_examples(source,task['public']+task['hidden'])
            if not row[condition]['available']: raise RuntimeError('Held-out evaluation unavailable; no fabricated fail/pass')
            visible = list(task['public'])
            if condition == 'tests': visible += qualification[name+'--tests']['qualified']
            row[condition]['visible'] = isolated_examples(source,visible)
        scores.append(row)
    summary = {'tasks':len(scores)}
    for condition in ('initial','review','tests'):
        summary[condition] = {'passed':sum(row[condition]['passed'] for row in scores),
            'visible_green_hidden_red':sum(row[condition]['visible'].get('passed') is True and not row[condition]['passed'] for row in scores)}
        if condition != 'initial':
            summary[condition].update(repaired=sum(not r['initial']['passed'] and r[condition]['passed'] for r in scores),
                                      regressed=sum(r['initial']['passed'] and not r[condition]['passed'] for r in scores))
    tests = [v for k,v in qualification.items() if k.endswith('--tests')]
    summary['test_feedback'] = {'submitted':sum(len(x['submitted']) for x in tests),
        'qualified':sum(len(x['qualified']) for x in tests),
        'rejected':sum(len(x['submitted'])-len(x['qualified']) for x in tests),
        'invalid_feedback':sum(not x['valid'] for x in tests),
        'incorrect_initials_passing_nonempty_generated_suite':sum(
            not row['initial']['passed'] and bool(qualification[row['task']+'--tests']['qualified']) and
            (qualification[row['task']+'--tests']['initial_candidate_execution'] or {}).get('passed') is True for row in scores)}
    summary['review_feedback'] = {'incorrect_initials_assessed_likely_correct':sum(
        not r['initial']['passed'] and (qualification[r['task']+'--review']['feedback'] or {}).get('assessment') == 'likely_correct' for r in scores)}
    trials = []
    for phase in ('initial','feedback','repair'):
        trials.extend(json.loads((ROOT/'evidence'/f'{phase}-receipt.json').read_text())['trials'])
    usage = [r['runner'].get('token_usage') or {} for r in trials]
    summary['resources'] = {'sessions':len(trials),'wall_seconds':execution['wall_seconds'],
        'models':sorted(set(r['runner']['native'].get('model') or 'unknown' for r in trials)),
        'known_total_tokens':sum((u.get('total') or {}).get('totalTokens',0) for u in usage),
        'missing_token_totals':sum('totalTokens' not in (u.get('total') or {}) for u in usage),
        'outer_orchestration_tokens':None,
        'response_observations':sum((r['runner'].get('inference_usage') or {}).get('response_count',0) for r in trials),
        'sessions_with_complete_response_accounting':sum((r['runner'].get('inference_usage') or {}).get('complete') is True for r in trials)}
    dump(ROOT/'results/scores.json',{'summary':summary,'tasks':scores})
    print(json.dumps(summary,indent=2))
    return summary


if __name__ == '__main__': report()
