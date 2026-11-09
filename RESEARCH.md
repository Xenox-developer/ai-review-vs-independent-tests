# Why this question

The operational question is how to spend an additional verification pass after
a coding agent produces a patch: written review or independently authored tests.
This pilot concerns one inference setup on eight authored tasks. It is not a
product comparison, a SWE-bench result or a claim about every engineering team.

Primary sources checked on November 9, 2026:

- [GitHub Octoverse 2026](https://github.blog/news-insights/octoverse/octoverse-commits-pushes-reach-new-highs-in-2026-as-developers-build-with-agents/),
  October 28, updated November 6. GitHub's reported growth of agent-originated
  pull requests motivates examining verification. Its platform adoption figures
  do not establish code correctness.
- [Anthropic Code Review GA](https://claude.com/resources/articles/code-review-is-now-generally-available),
  October 15. A relevant production product direction, not evidence that any
  review treatment outperforms tests in this pilot.
- [ExecCritic](https://arxiv.org/abs/2609.09133), September 8 preprint. The authors
  separate test construction from source repair and study how test quality affects
  repair. Our pilot uses no role-specific training, different tasks and a correct
  reference for test qualification; it does not reproduce their benchmark.
- [Teaching Agents to Code Reliably](https://arxiv.org/abs/2610.03984), October 2
  preprint. Includes investigation of false acceptance by patch-associated tests.
  Its reported benchmark gains are not our results.

Selection is an editorial judgment about practical relevance and feasibility.
These dates are disclosed research context, not a fresh-news roundup.

[INVARIANT](https://github.com/Xenox-developer/invariant) is the actual execution
and fixed public-validation tool used in this project. Fresh worker contexts,
case-scoped inputs and a separate held-out evaluator are experimental design
choices, not a claim of independent external replication or a tool safety guarantee.
