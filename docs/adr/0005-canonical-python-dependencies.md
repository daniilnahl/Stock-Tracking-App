# ADR-0005: Canonical Python dependency workflow

## Status

Accepted. On 2026-10-02, the repository owner approved SRS v1.1 and explicitly
authorized creating `pyproject.toml` from `reqs.txt` and current imports, making
it the master dependency file, and removing `reqs.txt` when unnecessary for
environment setup. Authorization was provided in the issue #2 implementation
chat. This record documents that decision; it does not approve other milestones.

## Context

At commit `3cc3298`, the repository had `reqs.txt`, no `pyproject.toml`, and no
supported-Python declaration in project configuration. README advertised
Python 3.6+, while the pinned NumPy and Matplotlib versions require newer Python.
DEV-003 incorrectly described a pre-existing `pyproject.toml` workflow.

## Decision

- Use setuptools with PEP 621 metadata and `python -m pip install .` from the
  checkout. Keep the flat application modules and existing CLI commands.
- Make `pyproject.toml` the single master dependency file. Remove `reqs.txt`
  after verifying that this installation path sets up the environment.
- Preserve the five direct-import pins: certifi, matplotlib, python-dotenv,
  Rich, and Typer. Preserve the existing transitive pins for reproducibility.
- Remove unused Requests, charset-normalizer, idna, and urllib3. Application
  HTTP calls use the standard-library urllib, not Requests. Retain certifi
  because `utils/utility_module.py` imports it directly.
- Declare Python `>=3.11,<3.13`. These versions remain supported by Python;
  3.13 removed the `cafile` argument used by the current HTTP implementation.
  Extending support requires a separate provider change and validation.
- Set package metadata version to the existing latest release tag `v1.1.0.1`.
- Correct DEV-003 explicitly. Preserve every requirement ID and all §23
  milestone content and exit criteria.

## Alternatives

Keeping a separately maintained requirements file would duplicate the master
dependency declaration. Introducing another package manager or relocating the
application is unnecessary for this decision. Updating dependency versions is
deferred to the tooling/security work rather than bundled with publication.

## Consequences

Environment setup uses pip and one dependency declaration. Full transitive pins
must be reviewed together when dependencies change. The application still
requires the checkout as its working directory for CSV and watchlist paths.
This change does not add pytest, Ruff, CI, provider repairs, or production
readiness; those remain M0 work. `docs/TESTING.md` and
`docs/FINANCIAL_CALCULATIONS.md` are referenced target deliverables and are not
published by this issue. Agent instructions are copied without rewriting them.

## Issue #5 implementation detail

The approved Python range, setuptools backend and pip workflow remain unchanged.
The `dev` extra extends the same exact-pin mechanism to pytest, Ruff, pytest's
additional transitive dependencies and wheel-building tools. Runtime pins supply
pytest's shared packaging/colorama dependencies. No second requirements or lock
file is maintained. Pins constrain versions on Python 3.11 and 3.12; they do not
guarantee artifact hashes or identical platform-specific wheel bytes. Pin updates
must be validated in fresh environments on both supported runtimes.

The original consequences above describe issue #2; issue #5 adds development
tools and packaging checks, while testing policy, baseline repairs and lint
configuration remain separate M0 deliverables.

## References

- [Issue #2](https://github.com/daniilnahl/Stock-Tracking-App/issues/2)
- [SRS approval and DEV-003](../../SRS.md)
- [Agent operating policy](../../AGENTS.md)
- [Python 3.13 urllib changes](https://docs.python.org/3.13/library/urllib.request.html)
- [Python version status](https://devguide.python.org/versions/)
