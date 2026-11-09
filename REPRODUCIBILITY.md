# Recalculate without inference

From a public clone:

```sh
python3 -m unittest discover -s tests -v
python3 verification/recalculate.py
```

The second command requires Docker and the original already-local Python image
recorded in lab/runtime.json. It does not start Codex or INVARIANT model sessions.
For another already-local Python 3.12 image with IANA timezone data:

```sh
python3 verification/recalculate.py --image YOUR_LOCAL_PYTHON_IMAGE
```

The scorer refuses automatic image pulls and reports whether the image matches
the original. It verifies all frozen input hashes and all 24 source-snapshot
hashes, independently executes literal expected examples, and compares aggregate
counts with results/scores.json. It uses unittest's normal ValueError-subclass
semantics; the frozen primary scorer uses exact exception names. Any difference
is reported, rather than silently replacing the original measurement. See
evidence/oracle-review-note.md.

On the original host, `python3 -m lab.report` reruns the frozen primary scorer.
`python3 -m lab.audit` verifies task/condition coverage, source hashes, 40 distinct
native threads, model/effort consistency and paired starting sources. The private
working-copy checks are available on that host; their public hash manifests are
in evidence/worker-input-manifests.json. `python3 -m lab.plot` renders PNG/SVG from
saved scores and needs requirements-plot.txt. No inference is used by these commands.

# Original measured execution

The commands in README's preparation sequence describe the original run BEFORE
evidence/frozen.json existed. A published clone intentionally refuses to overwrite
that frozen manifest or replay a saved execution. A new measurement requires a
new namespace/project copy with separate evidence and a new pre-measurement freeze;
keep the original evidence intact, pin the desired model and record new image IDs.
Do not present a fresh run with another account default as this same measurement.

Native INVARIANT studies, all medium effort with no automatic winner/application:

| Stage | Study | Scope |
|---|---|---|
| Initial | study-df8d9e868ee6422b80adc1ee788d7c24 | 8 implementation sessions; public behavioral checks |
| Feedback | study-766e4325812640fdb7cea40f8d041920 | 8 review + 8 independent-test sessions; artifact-format checks |
| Repair | study-710222efaf57439aa030b4c3c5b84fd3 | 16 repair sessions; public checks, plus frozen qualified tests in tests arm |

The protected feedback evaluator validates JSON structure, NOT substantive review
or test quality. Reference qualification and held-out outcome scoring run in
separate non-agent, offline Docker processes. Hidden tests/reference code never
enter a measured worker workspace or its protected public evaluator source.

Version, source commit, CLI identity, stage request IDs, receipts, input manifests,
model identities, provider usage observations and executor command witnesses are
recorded in evidence/. Private authentication/state/mounts are not published.

The recorded measurement wall time runs from initial study submission through the
last repair stage and artifact capture, including public checks and reference
qualification. Shared setup and later held-out scoring, audit and plotting are
outside that interval. Outer orchestration-chat usage is unavailable. Session
totals already include their provider response observations; never add the two.
Cached input and reasoning output are subsets of token totals, not extra tokens.
