"""Publish allowlisted execution facts, excluding authentication and private mounts."""
import hashlib
import json
from .prepare import ROOT, dump


def main():
    rows=[]
    for phase in ('initial','feedback','repair'):
        private=ROOT/'execution'/phase/'private-results.json'
        result=json.loads(private.read_text())
        for trial in result['trials']:
            runner=trial['runner']; runtime=runner.get('runtime') or {}
            rows.append({'phase':phase,'case_id':trial['case_id'],'attempt_id':trial['attempt_id'],
                         'runtime':{k:runtime.get(k) for k in ['image','resource_contract','host_config','memory_bytes','nano_cpus','pids_limit','network']},
                         'token_usage':runner.get('token_usage'),
                         'inference_usage':{k:v for k,v in (runner.get('inference_usage') or {}).items() if k!='path'},
                         'command_evidence':{k:v for k,v in (runner.get('command_evidence') or {}).items() if k!='path'}})
    comparable=[r['runtime']['host_config'] for r in rows if r['runtime']['host_config'] is not None]
    assert len(comparable)==40 and all(v==comparable[0] for v in comparable)
    assert all(r['runtime']['memory_bytes']==2048*1024**2 and r['runtime']['nano_cpus']==2_000_000_000 for r in rows)
    dump(ROOT/'evidence/runtime-resources-usage.json',{'resource_limits_match':True,'attempts':rows,
        'omitted':'Authentication, environment variable values, private mount paths and local native-home paths are not published.'})
    # Native exported log bundles contain synthetic task-only observations. Select
    # provider numeric usage journals; never export arbitrary session/auth files.
    ledgers={}
    for phase in ('initial','feedback','repair'):
        logs=ROOT/'execution'/phase/'.invariant/logs'
        if not logs.exists(): continue
        for path in logs.rglob('*.usage.jsonl'):
            observations=[]
            for line in path.read_text().splitlines():
                value=json.loads(line)
                if not {'sequence','usage','cumulative','attribution'} <= value.keys(): continue
                key=(phase,str(path.relative_to(logs)).split('export-')[-1].split('/',1)[-1])
                observations.append({k:value[k] for k in ['sequence','response_id','phase','timestamp','usage','cumulative','attribution'] if k in value})
            if observations:
                previous=ledgers.get(key,[])
                common=min(len(previous),len(observations))
                assert previous[:common]==observations[:common], 'Usage journal prefix changed'
                if len(observations)>len(previous): ledgers[key]=observations
    if ledgers:
        dump(ROOT/'evidence/provider-observations.json',{'journals':[{'phase':key[0],'path':key[1],'observations':value} for key,value in ledgers.items()]})
    commands=[]
    for row in rows:
        logs=ROOT/'execution'/row['phase']/'.invariant/logs'
        expected=row['command_evidence'].get('sha256')
        matches=[p for p in logs.rglob('runner.commands-*.jsonl') if p.parent.name==row['attempt_id']]
        if not matches:
            commands.append({'attempt_id':row['attempt_id'],'available':False});continue
        complete=[p for p in matches if hashlib.sha256(p.read_bytes()).hexdigest()==expected]
        assert complete, 'No exported command journal matches the saved final digest'
        facts=[json.loads(x) for x in complete[0].read_text().splitlines()]
        # Full executor command witnesses are synthetic task code in /workspace;
        # review these allowlisted exports for secrets before hosting the repo.
        commands.append({'attempt_id':row['attempt_id'],'phase':row['phase'],
                         'case_id':row['case_id'],'available':True,'sha256':expected,
                         'completed_executor_commands':len(facts),
                         'unrecorded_commands':row['command_evidence'].get('unrecorded_commands'),
                         'witnesses':facts})
    dump(ROOT/'evidence/executor-command-witnesses.json',{'attempts':commands,
        'total_tool_calls':None,'scope':'Executor command-completion events only; this is not a count of all tool types.'})
    groups={}
    for row in rows:
        group=row['case_id'].rsplit('--',1)[-1] if '--' in row['case_id'] else 'initial'
        groups.setdefault(group,[]).append(row)
    accounting={}
    for group,items in groups.items():
        accounting[group]={'sessions':len(items),'known_usage':{},'missing_fields':{}}
        for field in ['inputTokens','cachedInputTokens','outputTokens','reasoningOutputTokens','totalTokens']:
            values=[(item['token_usage'] or {}).get('total',{}).get(field) for item in items]
            accounting[group]['known_usage'][field]=sum(x for x in values if type(x) is int)
            accounting[group]['missing_fields'][field]=sum(x is None for x in values)
        accounting[group]['observed_responses']=sum(item['inference_usage'].get('response_count',0) for item in items)
        accounting[group]['complete_response_accounting_sessions']=sum(item['inference_usage'].get('complete') is True for item in items)
    dump(ROOT/'results/resource-accounting.json',{'groups':accounting,'outer_caller_usage':None,
        'notes':['Cached input and reasoning output are subsets, not additional tokens.',
                 'Initial baseline has fewer sessions than either complete feedback+repair treatment.',
                 'Unknown outer/shared setup usage is excluded; no dollar cost inferred from tokens.']})
    input_manifests=[]
    for phase in ('initial','feedback','repair'):
        project=ROOT/'execution'/phase
        recipe=json.loads((project/'experiment.json').read_text())
        dump(ROOT/'evidence/definitions'/f'{phase}.json',recipe)
        for case in recipe['cases']:
            files=[case['prompt_file'],case['input_file'],*[f['source'] for f in case['fixtures']]]
            input_manifests.append({'phase':phase,'case_id':case['id'],
                'files':{name:hashlib.sha256((project/name).read_bytes()).hexdigest() for name in files},
                'source_sha256':hashlib.sha256((project/next(f['source'] for f in case['fixtures'] if f['destination']=='solution.py')).read_bytes()).hexdigest()})
    dump(ROOT/'evidence/worker-input-manifests.json',{'cases':input_manifests})
    print(json.dumps({'verified_matching_resources':len(rows),'numeric_usage_journals':len(ledgers),
                      'command_journals':sum(row['available'] for row in commands)}))


if __name__=='__main__': main()
