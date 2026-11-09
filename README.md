# AI code review versus independent tests

An eight-task paired synthetic pilot comparing a fresh AI code review followed
by repair with independently authored behavioral tests followed by repair.
Status: implementation and protocol preparation; no measured results yet.

See [PROTOCOL.md](PROTOCOL.md) for conditions, blinding, matched settings,
oracle-assisted test qualification, outcomes and limitations. A green public
test is not the primary correctness outcome. Held-out checks remain outside
all model-visible workspaces, then are published for reproducibility.

## Requirements

Python 3.12+, a running Docker engine with the existing Python base image
pinned in lab/runtime.json for separate held-out evaluation,
INVARIANT 0.3.1 and its supported Codex CLI authenticated through an existing
subscription. No paid API, GPU rental, additional subscription or model download.
The actual account model is recorded in execution receipts, not guessed here.
Matplotlib is used only to render measured figures after completion.

## Commands

```sh
python3 -m unittest discover -s tests -v
python3 -m lab.prepare
git add . && git commit -m 'Freeze paired verification protocol'
python3 -m lab.run --execute
python3 -m lab.report
```

`lab.prepare` freezes hashes and builds the initial case-scoped workspace.
`lab.run --execute` consumes subscription usage: a planned 40 fresh worker
sessions, potentially multiple model responses per session. It refuses to
overwrite previous measurements or replay uncertain attempts. INVARIANT executes
the native studies, isolated tools and protected public acceptance checks.
No candidate is automatically applied to this host repository.

`lab.report` reruns only deterministic Docker checks on saved candidate sources;
it performs no inference. Published sources, feedback and structured receipts
live in evidence/, derived outcomes in results/. Private .invariant/ state and
execution/ working copies are excluded from Git.

All tasks/examples/reference implementations were authored for this experiment
and licensed MIT. This is not a reproduction of ExecCritic or an assessment of
production review products. Eight small tasks cannot establish an industry-wide
winner, and the initial implementation may produce a ceiling result.

Tool: [INVARIANT](https://github.com/Xenox-developer/invariant).
Research context: [ExecCritic](https://arxiv.org/abs/2609.09133),
[Teaching Agents to Code Reliably](https://arxiv.org/abs/2610.03984).
