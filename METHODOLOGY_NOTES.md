# Interpretation boundaries

These notes clarify the frozen design; they do not change tasks, prompts,
selection, qualification, repairs or scoring after measurement begins.

- The benchmark contracts, starter code, references and literal expected examples
  were authored by the orchestrating AI before measured worker sessions. References
  were checked against literal expectations and original defective starters were
  negative controls. There is no independent human/external validation of this
  synthetic benchmark; shared model-family errors remain possible.
- “Independent tests” means a fresh worker context with the candidate patch
  withheld. It does not mean a different model, independently collected production
  data or independent scientific replication.
- Reviewers may execute the candidate and focused checks, but deliver written
  feedback. Test authors see the original incomplete starter and deliver executable
  input/expected-output examples. Both repairs receive the complete specification.
  The interventions differ in feedback form, access and reference qualification;
  this pilot cannot isolate one of those mechanisms as the cause of any difference.
- The reference qualifier is itself an oracle-assisted treatment. Matching a
  reference on a submitted example is not proof the generated test captures the
  entire contract, and qualification is not always available in production.
- There is one trivial public example per task. The primary fixed evaluation has
  54 held-out examples plus those 8 regression examples, each checking the result
  and input nonmutation. Counts of examples are not counts of independent tasks.
- A task passes these finite examples, rather than being proved correct for all
  inputs. Review issues on a passing task are not automatically false positives.
- A ceiling outcome must remain a ceiling outcome. Do not add harder cases,
  inject defects into saved candidates or rerun seeds to produce a preferred winner.
