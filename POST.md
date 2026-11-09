I compared AI code review with tests written without seeing the candidate patch.

Eight small Python tasks. One initial gpt-6.1-sol patch per task, followed by two fresh-context workflows: review → repair and independent tests → repair. Same model, medium reasoning, identical per-session deadlines.

The frozen checker scored:
• Initial patches: 7/8
• Review → repair: 7/8
• Tests → repair: 8/8

The entire gap came from one exception check.

A path-validation task used strict UTF-8 decoding and ValueError for rejected paths. The candidate raised UnicodeDecodeError, which is already a ValueError subclass. My checker compared exact class names and marked it wrong. The test-guided repair added a wrapper that raised ValueError directly.

A separate evaluator using normal assertRaises(ValueError) semantics scored all three conditions 8/8. The apparent improvement came from the stricter grader. This pilot doesn't establish an advantage for either workflow.

The run used 40 isolated Codex sessions and 230 generated test examples, qualified against a frozen reference. INVARIANT coordinated the sessions and protected public checks; held-out scoring ran separately. Both original and supplementary scoring reports are preserved.

These were AI-authored synthetic tasks, one model and finite checks. Reference qualification also gives the testing workflow an oracle that may be unavailable in production. The initial patches already passed this set under normal exception handling.

Code, artifacts and both reports:
https://github.com/Xenox-developer/ai-review-vs-independent-tests

Tool used — INVARIANT:
https://github.com/Xenox-developer/invariant

Python exception hierarchy:
https://docs.python.org/3.12/library/exceptions.html#UnicodeError

#AIEngineering #LLMTesting
