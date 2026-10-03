# Issue #3: owner credential-rotation attestation

Related issue: [#3](https://github.com/daniilnahl/Stock-Tracking-App/issues/3)

Requirements: SEC-004 (rotate exposed secrets outside the codebase) and
SEC-001 (no active credentials in source control).

## Owner confirmation

On 2026-10-02 (America/Los_Angeles), the repository/provider owner confirmed
in the implementation chat that the revocation and replacement steps were
completed, then confirmed "key is set" and authorized proceeding.

This records the owner's attestation that all exposed FMP credentials were
revoked and a replacement was generated and stored outside source control
in a local Windows user environment variable named `FMP_API_KEY`. The
replacement was not supplied to the agent or included in this document,
source, fixtures, logs, or PR text.

Revocation and local storage are owner-attested, not independently verified
by the agent. No automated credential verification or live provider request
was performed.

## Sanitized location inventory

The tracked baseline is commit `3cc3298`. A read-only inspection emitted
only filenames, line numbers, and configuration-variable names:

- `test.py`: credential/configuration references at lines 21, 23, 25, 26,
  and 30. The issue identifies this scratch script as containing a
  credential literal and credential-bearing example URLs.
- `.env`: tracked local environment file with a configuration reference at
  line 1. Being listed in `.gitignore` does not untrack an existing file.
- `menu_watchlist.py` and `daniils_stock_method.py`: legacy callers read
  `MY_API_KEY` and pass the credential into application objects.
- `stock.py` and `utils/utility_module.py`: legacy credential/request
  references. These are potential propagation locations, not evidence of
  additional distinct exposed key values.

Git history for `test.py` and `.env` was inspected by commit identifier
only; no historical credential values were printed or copied. This inventory
is not a comprehensive historical secret scan. The owner attestation covers
all exposed values, including previously committed credentials.

## Remaining work and boundaries

- Issue [#4](https://github.com/daniilnahl/Stock-Tracking-App/issues/4) owns
  source sanitization, untracking `.env` while preserving the local file,
  and redacted tracked-source scanning. That issue remains open at the time
  of this record; its scanning results must be referenced after completion.
- Issue [#7](https://github.com/daniilnahl/Stock-Tracking-App/issues/7) owns
  the configuration loader and preserves `MY_API_KEY` compatibility.
  `FMP_API_KEY` records the owner's current storage location; the existing
  CLI does not read that name. No configuration integration is claimed here.
- Source cleanup, credential propagation into legacy persisted objects,
  and the overall M0 security exit criteria are not completed by this record.
- No Git history was rewritten. Any historical secret-removal decision
  requires a separately authorized task.
- The agent did not rotate credentials, change provider permissions or
  billing, run live tests, or merge a pull request.

## Verification

Manual owner attestation is the verification required by issue #3.
Documentation was reviewed for scope, accurate attribution, and absence of
credential values. `git diff --check` validates patch whitespace.

Application pytest, Ruff, and type checks were not run: this change adds
only an attestation document, and issue #3 explicitly requires no automated
credential verification or live provider requests. No application behavior
or test configuration is changed.
