# AGENTS.md

## Purpose

This file defines how AI coding agents are allowed to operate in the Stock Tracking App repository.

The goal is to produce changes that are:

- bounded
- testable
- reviewable
- reversible
- traceable

Agents operate as implementation engineers. They do not independently redefine product requirements or architecture.

---

# 1. Authority and Source of Truth

Product and operational authority are separate.

## 1.1 Product behavior authority

Use this precedence:

1. Approved `SRS.md`
2. Accepted ADRs under `docs/adr/`
3. Approved GitHub issue/task
4. Existing tests that reflect approved behavior
5. Existing implementation
6. README and older documentation

A GitHub issue may narrow or implement an SRS requirement, but MUST NOT silently contradict the SRS or an accepted ADR.

If an issue intentionally changes the specification, it must explicitly identify itself as a specification change and require human approval.

## 1.2 Agent operating authority

Use this precedence:

1. `AGENTS.md`
2. Explicit human instructions for the current task
3. Repository tooling/configuration
4. Existing conventions

A task instruction cannot authorize unsafe destructive behavior merely by implication.

## 1.3 Conflict handling

When authoritative sources materially conflict:

1. Stop the conflicting portion of implementation.
2. Do not invent a resolution.
3. Record the conflict.
4. Request human review.

---

# 2. Required Reading

Before editing code:

1. Read `AGENTS.md`.
2. Read relevant `SRS.md` sections and requirement IDs.
3. Read relevant ADRs.
4. Read `docs/TESTING.md`.
5. Read `docs/FINANCIAL_CALCULATIONS.md` if financial behavior is involved.
6. Read the relevant implementation.
7. Search for callers of anything being changed.
8. Read associated tests.

Do not modify a public interface without checking its downstream callers.

---

# 3. Project Priorities

Prefer, in order:

1. Correctness
2. Security
3. Data integrity
4. Testability
5. Architecture consistency
6. Backward compatibility
7. Maintainability
8. Performance
9. New features

For financial calculations, correctness takes priority over presentation or implementation convenience.

---

# 4. Agent Permission Matrix

Unless the current task explicitly says otherwise:

| Action | Permission |
|---|---|
| Read source, tests, docs | YES |
| Edit source | YES |
| Edit tests | YES |
| Edit task-relevant docs | YES |
| Create a feature/fix branch | YES |
| Commit to task branch | YES |
| Push task branch | YES |
| Open pull request | YES |
| Create follow-up issue | YES, when supported and clearly useful |
| Merge pull request | NO |
| Push directly to `main` | NO |
| Force-push | NO |
| Alter branch protection | NO |
| Rotate/revoke credentials | NO — human/external action |
| Use live production credentials | NO |
| Delete user data | NO |
| Perform destructive migration | NO without explicit approval |
| Modify CI | ONLY when task scope requires it |
| Add project dependency | ONLY when justified by task |
| Install/alter system software | NO unless explicitly authorized |
| Change Python version | NO unless explicitly authorized |
| Introduce new package manager | NO without approved ADR |
| Change public API/CLI contract | NO unless requirement authorizes it |

If a required action is not authorized, escalate rather than working around the restriction.

---

# 5. Scope Control

Implement only the assigned issue or task.

Do not perform unrelated:

- refactoring
- dependency replacement
- file renaming
- formatting of untouched modules
- feature additions
- CLI redesign
- architecture redesign
- documentation rewrites

If an unrelated defect is discovered:

1. Do not fix it unless it directly blocks the task or creates an immediate security/data-integrity risk.
2. Record it in the PR.
3. Create or recommend a follow-up issue when appropriate.

Prefer the smallest coherent diff that satisfies the acceptance criteria.

---

# 6. Architecture Boundaries

Respect `SRS.md` architecture requirements.

## Domain layer

May contain:

- stocks
- positions
- portfolios
- typed domain models
- validation
- financial calculations defined by specification

Must not contain:

- API credentials
- HTTP requests
- SQL
- terminal formatting
- CLI prompts
- environment access

## Market-data layer

May contain:

- provider adapters
- HTTP
- response parsing
- retry/rate-limit behavior
- provider-specific models

Application services depend on provider interfaces rather than provider URLs or payload structures.

## Persistence layer

May contain:

- repositories
- SQLite
- schema/migration code
- persistence-specific mappings

Domain objects must not open database connections or issue SQL.

## Presentation layer

May contain:

- Typer commands
- Rich formatting
- human-readable messages
- chart rendering

Presentation code must not become the source of financial business logic.

---

# 7. Financial Rules

Before implementing or changing a financial metric:

1. Find its definition in `docs/FINANCIAL_CALCULATIONS.md`.
2. Confirm the formula, units, rounding, missing-data behavior, and market-data inputs.
3. Add known-value tests.
4. Preserve numeric values internally.
5. Format only at presentation boundaries.

If the metric is missing or ambiguous, STOP that part of the task and escalate.

Do not invent:

- return conventions
- cost-basis methods
- dividend treatment
- split treatment
- FX conversions
- benchmark alignment rules

---

# 8. Security Rules

Never commit or expose:

- API keys
- tokens
- passwords
- credentials
- secrets in fixtures
- private credential-bearing URLs

Secrets come from environment variables or an approved secret store.

Before committing:

1. Inspect staged changes.
2. Check for accidental secrets.
3. Check that logs and test fixtures contain no real credentials.

Previously committed credentials must be treated as compromised.

Never log secrets.

Use parameterized SQL.

Do not deserialize untrusted arbitrary Python objects.

---

# 9. Development Environment

Use the repository's existing canonical setup.

Do not independently introduce:

- Poetry
- uv
- pip-tools
- Conda
- a second lockfile system
- a second formatter/linter
- a second migration framework

unless an approved task/ADR requires it.

Do not change the supported Python version without explicit approval.

If the documented environment cannot be reproduced, record the exact failure rather than silently replacing the toolchain.

---

# 10. Milestones and GitHub Issue Decomposition

GitHub Milestones are planning containers. They are NOT implementation tasks.

An agent responsible for planning work MUST decompose an approved SRS milestone into multiple bounded GitHub issues before implementation begins.

The default hierarchy is:

```text
SRS
  -> GitHub Milestone
      -> GitHub Issue
          -> Branch
              -> Pull Request
                  -> Tests
```

## 10.1 Milestone creation

For each approved SRS milestone, create or use one corresponding GitHub Milestone.

Recommended naming:

```text
M0 — Security & Foundation
M1 — Domain Refactor
M2 — Market Data Layer
M3 — Persistence
M4 — Historical Market Data
M5 — Portfolio Analytics
M6 — CLI V2
M7 — REST API
M8 — Web Dashboard
```

The milestone description SHOULD include:

- goal
- relevant SRS sections / requirement IDs
- exit criteria
- dependencies
- known blockers

Do NOT create one large GitHub issue representing the entire milestone.

## 10.2 Issue decomposition

Each milestone MUST be decomposed into atomic engineering issues.

Default rule:

```text
1 issue
≈ 1 bounded engineering objective
≈ 1 branch
≈ 1 pull request
```

A good issue should normally be implementable and reviewable independently.

Good examples:

```text
Create MarketDataProvider protocol
Implement FMP quote retrieval
Add retry handling for transient provider failures
Introduce Portfolio domain model
Implement SQLite PortfolioRepository
Add GitHub Actions test workflow
```

Bad examples:

```text
Finish market data layer
Complete milestone 2
Refactor the whole application
Build the backend
Improve tests
```

## 10.3 Issue requirements

Every implementation issue SHOULD contain:

```markdown
## Problem
What is wrong or missing?

## Goal
What observable result should exist when complete?

## Requirements
Relevant SRS requirement IDs.

## Scope
What may be changed.

## Out of Scope
What must not be changed.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Tests Required
What automated verification is expected.

## Dependencies
Blocking issues or PRs.
```

An issue MUST reference its parent GitHub Milestone.

## 10.4 Dependency ordering

Issues SHOULD be ordered by stable dependency direction:

```text
specification / contracts
        ↓
interfaces
        ↓
implementations
        ↓
application integration
        ↓
presentation
```

An agent MUST NOT begin work on an issue whose blocking dependency is unresolved unless explicitly authorized.

## 10.5 Planning horizon

Do not fully decompose every future milestone at the beginning of the project.

Preferred planning depth:

- Current milestone: detailed implementation-ready issues
- Next milestone: coarse issue candidates or placeholders where useful
- Later milestones: keep primarily at SRS/milestone level until architecture stabilizes

This prevents early assumptions from becoming unnecessary constraints.

## 10.6 Issue-to-PR rule

The default execution model is one issue to one PR.

Multiple issues MAY share one PR only when:

- they are very small
- they modify the same narrow concern
- they have no meaningful independent review value
- combining them does not obscure traceability

A single issue MAY require multiple PRs when the change is too large to review safely. In that case, split the issue or create child/follow-up issues before implementation.

## 10.7 Milestone completion

A milestone is complete only when:

- all required issues are closed
- required CI checks pass
- milestone exit criteria from `SRS.md` are satisfied
- no blocking issue remains open
- any deferred work is captured in explicitly assigned follow-up issues

Closing a milestone is a planning action and MUST NOT be used to hide incomplete requirements.

---

# 12. Branching

Do not work directly on `main`.

Use short-lived branches:

```text
feature/<issue-number>-<description>
fix/<issue-number>-<description>
refactor/<issue-number>-<description>
test/<issue-number>-<description>
docs/<issue-number>-<description>
```

Typical setup:

```bash
git checkout main
git pull origin main
git checkout -b <branch-name>
```

Do not overwrite unrelated human or agent changes.

Avoid destructive Git operations.

`git reset --hard`, forced checkout, history rewriting, and force push are prohibited unless a human explicitly authorizes them for the current task.

---

# 12. Implementation Workflow

For each task:

1. Read the issue and acceptance criteria.
2. Identify referenced SRS requirement IDs.
3. Read relevant documentation and ADRs.
4. Inspect source and callers.
5. Inspect existing tests.
6. Write a minimal implementation plan.
7. Implement the smallest required change.
8. Add/update tests.
9. Run targeted tests.
10. Run the full required verification suite.
11. Inspect final diff.
12. Check for secrets and generated artifacts.
13. Commit logically.
14. Push branch.
15. Create PR.
16. Report assumptions, verification results, and unresolved concerns.

---

# 13. Testing Rules

Follow `docs/TESTING.md`.

Tests are part of implementation.

Unit tests must not require:

- live internet
- current stock prices
- current date/time unless controlled
- the user's real database
- execution in a specific order

When fixing a bug, add a regression test whenever practical.

Do not weaken valid tests simply to get green CI.

Do not:

- delete a failing test without justification
- modify expected values to bless wrong behavior
- use broad mocks that bypass the behavior under test
- add unconditional skips to hide failures
- swallow exceptions
- make production code incorrect to satisfy an inaccurate fixture

---

# 14. Verification Sequence

Use the canonical repository commands.

Typical sequence:

```bash
pytest <targeted-test-path> -v
pytest
ruff check .
mypy src/
```

Only run `mypy` if configured by the repository.

Before creating the PR:

```bash
git diff main...HEAD
git status
```

Do not claim a check passed unless it actually ran successfully.

If a required tool is not configured or available, report:

```text
Not verified: <tool/check>
Reason: <specific reason>
```

---

# 15. Determinism Rules

Tests MUST be deterministic.

When behavior depends on time:

- inject or patch the clock
- use fixed dates/timestamps
- account explicitly for market holidays/weekends in test fixtures

When behavior depends on randomness:

- use deterministic seeds

When behavior depends on persistence:

- use isolated temporary databases

When behavior depends on external APIs:

- use controlled fixtures/mocks

Do not make a test pass merely because today's market happens to be open.

---

# 16. Failure Recovery

Failure is expected. Uncontrolled recovery is not.

## 15.1 Targeted test failure

1. Read the full traceback.
2. Identify the failing assertion or exception.
3. Determine whether the current change caused it.
4. Fix the smallest root cause.
5. Re-run the affected test.
6. Run related tests.

Do not immediately rewrite large sections.

## 15.2 Full-suite regression

If targeted tests pass but the full suite fails:

1. Identify the regressed behavior.
2. Search callers of modified interfaces.
3. Check whether a breaking change is authorized.
4. Restore compatibility when it is not.
5. Add/update regression coverage.
6. Re-run full verification.

## 15.3 Lint/type failure

Fix the actual source issue.

Do not globally disable a rule to avoid fixing one failure.

Use narrow suppressions only when justified and documented.

## 15.4 Provider/mocking failure

Check:

1. request parameters
2. response fixture/schema
3. parser behavior
4. timeout/error mapping
5. mock correctness

Do not change production behavior solely to match an inaccurate mock.

---

# 17. Repeated Failure Policy

If an implementation approach repeatedly fails:

1. Stop speculative patching.
2. Re-read the requirement.
3. Re-read relevant source/tests.
4. Inspect the diff from the last coherent state.
5. Reduce to the smallest reproducible problem.
6. Try a materially different approach only after understanding the prior failure.

After three materially different unsuccessful attempts, **or earlier if continued changes increase security, architecture, regression, or data-loss risk**:

1. Stop expanding the diff.
2. Preserve diagnostics.
3. Return the branch to a coherent state when possible.
4. Document:
   - failing command
   - failing test
   - error summary
   - suspected root cause
   - approaches attempted
   - files involved
5. Escalate for human review.

The number three is a default ceiling, not permission to make three dangerous attempts.

---

# 18. Partial Completion

If the task cannot be completed:

- keep the branch buildable where possible
- do not claim completion
- identify unmet acceptance criteria
- do not merge
- document continuation notes

A smaller correct partial result is preferable to a larger unstable one.

---

# 19. Database and Migration Safety

Before changing schema:

1. Read persistence requirements and relevant ADRs.
2. Confirm the repository's single migration mechanism.
3. Determine whether existing user data is affected.
4. Add migration tests where relevant.
5. Use transactions when atomicity is required.

Never silently delete user data.

Never run destructive migration commands against a user's real database as part of automated tests.

If a destructive change appears necessary, stop and require explicit approval.

---

# 20. Error Handling

Prefer explicit application/domain exceptions.

Do not use:

```python
except Exception:
    pass
```

without a documented reason.

Do not swallow infrastructure failures.

Translate provider/database errors into application-level errors where useful.

CLI code may render those errors to users.

---

# 21. Logging

Use Python `logging` for diagnostics.

Do not add production diagnostic `print()` calls.

Never log secrets.

Avoid logging large provider payloads at normal log levels.

---

# 22. Dependency Changes

Before adding a dependency:

1. Confirm existing dependencies/stdlib cannot reasonably solve the task.
2. Explain why the dependency is needed.
3. Use the existing dependency-management mechanism.
4. Add/update tests.
5. Update docs if developer setup changes.
6. Consider maintenance/security/license implications when material.

Do not replace an existing dependency solely based on preference.

---

# 23. Commit Rules

Prefer Conventional Commits:

```text
feat: add market data provider abstraction
fix: reject ticker when validation request fails
refactor: separate portfolio logic from CLI
test: add portfolio return regression tests
docs: document environment configuration
chore: configure ruff
```

Avoid meaningless messages such as `updates`, `changes`, or `fix stuff`.

Do not commit:

- `.env`
- local caches
- IDE state
- temporary databases
- temporary debugging files
- generated artifacts not required by the repository

---

# 24. Pull Request Creation

One logical task should normally produce one PR.

Before opening a PR, run all required checks.

Push:

```bash
git push -u origin <branch-name>
```

Create a PR with the repository's template or equivalent GitHub CLI flow.

Do not merge your own PR unless explicitly instructed.

Do not bypass branch protection or required checks.

---

# 25. Pull Request Content

Each PR should include:

## Summary

What changed and why.

## Requirements

```text
Implements: <SRS requirement IDs>
```

## Related Issue

```text
Closes #<issue>
```

when appropriate.

## Changes

Meaningful implementation changes.

## Architecture Impact

Interfaces, dependencies, persistence, public contracts.

## Testing

Commands actually executed and results.

## Manual Verification

Manual checks, if relevant.

## Breaking Changes

`None` or explicit description.

## Security Considerations

`None` or explicit description.

## Agent Notes

- assumptions
- unresolved questions
- follow-up work
- deliberate technical debt

---

# 26. Pull Request Self-Review

Review the diff as if reviewing another engineer.

Check for:

- unrelated edits
- duplicated logic
- unnecessary abstractions
- accidental public API changes
- missing validation
- missing error paths
- test gaps
- dead code
- debug output
- hard-coded credentials
- incorrect financial arithmetic
- unsafe SQL
- inconsistent naming
- unrequested dependency/tooling changes

If the diff cannot be explained clearly, simplify it before submission.

---

# 27. Definition of Done

A task is complete only when:

- acceptance criteria are satisfied
- referenced SRS requirements are satisfied
- scope is controlled
- tests are added/updated when needed
- targeted tests pass
- full test suite passes
- linting passes
- type checking passes when configured
- no secrets are introduced
- no user data is endangered
- documentation is updated when behavior changes
- final diff is reviewed
- PR is created
- PR references the issue
- assumptions and unresolved concerns are documented

If a required check fails, the task is not complete.

---

# 28. Escalation Conditions

Stop and request human review when:

- requirements materially conflict
- a requested metric is undefined
- an unapproved breaking change appears necessary
- a migration may destroy user data
- credential rotation or other external security action is required
- repeated repair attempts fail
- an external API contract cannot be verified
- a task requires substantial unrelated refactoring
- intended test behavior is unclear
- a live production action would be required
- project tooling/environment cannot be reproduced

Do not invent product decisions merely to continue.

---

# 29. Parallel Agent Work

Parallel work is safe only with stable, non-overlapping contracts.

Good:

```text
Agent A -> SQLite repository implementation
Agent B -> FMP provider implementation
Agent C -> analytics test fixtures
```

Risky:

```text
Agent A -> redesign Portfolio API
Agent B -> build CLI against the old Portfolio API
```

If another branch is changing an interface required by the current task, coordinate around an agreed contract or wait for stabilization.

---

# 30. Final Agent Report

Use:

```text
Implemented:
- ...

Requirements:
- ...

Verification:
- pytest ...
- ruff check .
- mypy src/ ...

Not verified:
- ...

Assumptions:
- ...

Unresolved:
- ...

Follow-up:
- ...

Pull request:
- <URL>
```

Keep the report factual.

Do not claim completion while required checks or acceptance criteria remain unresolved.

---

# 31. Guiding Principle

Prefer:

- simple over clever
- explicit over implicit
- reviewable over broad
- reversible over destructive
- specified behavior over invented behavior

The agent's job is to reduce uncertainty, not create more of it.
