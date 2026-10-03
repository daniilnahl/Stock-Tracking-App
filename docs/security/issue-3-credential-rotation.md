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

### Current source and configuration review — 2026-10-03

At audited `main` commit `e0bbeb1`, issues #4, #7 and #17 are closed.
`.env` is untracked; `.env.example` contains only an empty `FMP_API_KEY`
assignment. Both CLI modules and the explicit scratch script use the shared
`config.py` loader, with canonical-name precedence and absent-only legacy
fallback. Configuration representations, missing-key messages and mapped
request diagnostics are covered by offline synthetic-credential tests.

The Credential patterns check passed on the
[audited main Foundation run](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37149517565).
It scans tracked index files for the known issue #4 literal and URL patterns,
with redacted findings. It does not certify arbitrary secret formats or
historical commits. The original inventory, integration note and verification
below retain their historical meaning; source sanitization and shared loading
have since been implemented.

The owner's rotation attestation remains the evidence for external revocation;
no credential was retrieved or tested against the provider during this review.
Legacy `Stock.API_KEY` and pickle persistence still carry credentials at runtime,
as explicitly bounded by issue #7; removing that coupling belongs to M1/M3.
See the [M0 verification record](../milestones/m0-verification.md) for the
complete security exit assessment and formal milestone status.

### Configuration integration update — issue #17

The issue #17 change makes both legacy CLI scripts and explicit scratch-script
execution read `FMP_API_KEY`. Current setup instructions and `.env.example` use
that canonical name. `MY_API_KEY` remains a compatibility fallback only when
`FMP_API_KEY` is absent after optional dotenv loading; an empty canonical value
does not fall back. For the same variable, the process environment overrides
dotenv. The inventory and remaining-work statements above describe the state
at the time of the original attestation and are preserved as historical facts.
This naming correction does not complete the shared configuration loader in #7
or remove credential propagation into legacy domain/persistence objects.

### Original attestation verification

Manual owner attestation is the verification required by issue #3.
Documentation was reviewed for scope, accurate attribution, and absence of
credential values. `git diff --check` validates patch whitespace.

Application pytest, Ruff, and type checks were not run: this change adds
only an attestation document, and issue #3 explicitly requires no automated
credential verification or live provider requests. No application behavior
or test configuration is changed.
