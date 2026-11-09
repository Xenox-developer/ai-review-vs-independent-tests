# AI review versus independently constructed tests

Pre-registered exploratory paired pilot, authored 2026-11-09 before inference.
Eight synthetic Python contracts, authored starter implementations, literal
held-out examples and separate reference implementations. No public benchmark
or production repository is being reproduced. Each solution exports `solve(data)`.

## Design

1. One fresh Codex/medium session implements each contract from the starter.
2. Branch that identical saved source into review and independent-tests arms.
   Review receives the candidate. Test construction receives the ORIGINAL starter,
   specification and public examples; it never receives the candidate.
3. Qualify each generated test against the frozen reference. Record every rejected
   or unexecutable test; retain all original feedback. Only reference-passing
   tests are supplied for repair. Qualification is an additional oracle-assisted
   component of the tests treatment, not a universally available production tool.
4. A fresh Codex/medium session per arm repairs the same initial candidate with
   its feedback. No iterative conversations between feedback author and repairer.
5. Score baseline and repaired source against the same frozen public + hidden
   literal examples and input nonmutation checks. A task passes only if all pass.

The initial candidate is a descriptive baseline, NOT a budget-matched third arm.
Each treatment has one feedback and one repair session per task. Maximum 40
native worker sessions total: 8 initial, 16 feedback, 16 repair. A session may
contain multiple model responses/tool calls. Count the available native token
totals separately; never call sessions generations. The surrounding orchestration
chat's usage is not available and is excluded, including shared preparation.

Each session: account-default Codex model resolved by INVARIANT, medium effort,
180-second per-session runner deadline, 2 CPUs/2048 MiB, one active trial,
15-second fixed evaluator timeout. These equal per-condition operational settings
prevent hung sessions; they are not a daily quota. The user removed artificial
daily generation and overall duration caps before measurement on 2026-11-09.
There is no global wall-time cap. Retain partial outcomes; do not relaunch
timed-out trials or replace models. A partial run is not a completed pilot.

Task order and within-task branch order are generated with Python Random seed
20261109 before measurement. Use identical order for feedback and repair stages.
This interleaves treatments by task instead of running all review work first.
No additional inference for a safety reviewer/application is requested: this is
an INVARIANT native comparison, with protected fixed evaluation and no application
or automatic winner selection. The experimental review is the measured feedback
arm; it does not authorize changes to the host repository.

## Blinding and intervention differences

Only check.py plus ACTIVE task fixtures enter a worker workspace. The fixed
evaluator source has no hidden examples or reference implementation. Each case's
read-only input contains its public examples and qualified tests when applicable.
Other case fixtures are coordinator inputs, not a mounted workspace. No worker
receives the main experiment repository, oracle/reference module, aggregated
results, other arms' feedback or other candidate patches. Network commands are
disabled. Saved artifact delivery and protected evaluation use INVARIANT.

Feedback validators establish artifact FORMAT, not substantive correctness.
Solution validation checks the public examples and, in the tests-repair arm,
qualified generated tests. This stricter visible suite is part of that treatment.
The hidden outcome is evaluated by a separate non-agent Docker process after
the measured sessions are terminal. Gold results are never returned to workers.
Publish hidden tests and references only after measurements finish.

Tests are qualified individually without inspecting outcomes of the measured
candidate; rejected expected answers are not corrected. Empty/invalid feedback
is retained and supplied as an empty qualified set with an explicit error. Repair
still receives the full specification. A malformed review is similarly retained
and represented as unavailable feedback. Missing initial source blocks both
arms of that task; missing terminal repairs remain missing, never passes.

## Frozen outcomes

Primary: number of tasks passing all held-out + regression checks per arm, paired
by task. Also publish all per-task outcomes. Count baseline-to-final repairs and
new regressions by task; multiple test cases are NOT independent observations.
Secondary: generated tests submitted/qualified/rejected, false rejection of the
reference, incorrect initial candidates that pass all qualified tests, reviewer
likely_correct assessments on incorrect initial candidates, visible-green but
hidden-red candidates, missing feedback, timeouts and run errors. Empty qualified
sets are unavailable coverage, never counted as a successful test verification.

No significance or industry-wide ranking from eight authored tasks. Null,
ceiling and negative outcomes are valid. No new cases, repaired oracles, reruns,
cherry-picked seeds or changed prompts after viewing outcomes. Oracle problems
invalidate affected tasks and require a separately labelled future protocol.

## Execution evidence and publication

Keep frozen hashes/tested commit, generated sources, raw feedback, qualification
records, stage definitions, INVARIANT identifiers/version, validation verdicts,
available usage and model identities. Zero paid API calls, no new model downloads
or GPU rental. Chart text contains metric/condition labels and numbers only.
English LinkedIn draft links the dedicated repository and INVARIANT and states
sample size, treatment differences and limitations. Do not publish incomplete
measurements as results. Existing daily publication cap/queued news remain in force.
