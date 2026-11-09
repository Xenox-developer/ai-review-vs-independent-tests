# Exception-class interpretation, identified before held-out scoring

During static review of the frozen checker, before reading candidate source or
running held-out scoring, a possible contract interpretation difference was
identified. check.py matches the exact exception class name `ValueError`.
Python's usual `assertRaises(ValueError)` also accepts subclasses, such as
UnicodeDecodeError from strict percent decoding in the safe-path contract.

Do not change frozen examples, prompts, candidates, repairs or the primary
checker. The separately implemented verification/recalculate.py uses normal
assertRaises semantics. If classifications disagree, retain both outcomes,
identify the affected cases and report the discrepancy as an oracle limitation;
do not quietly replace the primary result or claim verified agreement. If all
candidate classifications agree, the interpretation difference did not change
this run's measured task outcomes.
