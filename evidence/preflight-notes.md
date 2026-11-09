# Before the first model call

The first local setup invocation stopped at `invariant init --json`: INVARIANT
0.3.1 rejects JSON mode for init. No study was submitted, no execution.json was
created and no model session was started. Use text-only init, keeping JSON mode
for supported config/experiment commands. Protocol hash manifest was revised
before measurement; the original manifest/commit remains in version history.

The standalone held-out-check preflight initially selected the INVARIANT Python
launcher image, whose entry point expects the tool's managed environment. That
is not a general-purpose Python command image. Before freezing measurements,
the separate non-agent evaluator was configured to use an already-installed
Python 3.12.15 base image by immutable local ID; no download and no override of
INVARIANT worker validation were used. All eight correct references passed all
62 literal checks in that offline evaluator before the first measured call.
