# Changelog

## 0.2.1 — security hardening

- Restricted Local Operator CORS responses to the Chrome extension origin and localhost origins.
- Added an OPTIONS origin check.
- Added regression coverage for sensitive/irreversible terms.
- Re-ran unit tests, compile checks, and local API health checks.

This package remains analysis-only: it does not control browsers, submit forms, handle credentials, solve CAPTCHAs, place bets, or perform transactions.

## 0.3.0 — action policy

- Added a deny-by-default Action Policy Engine.
- Added `/policy` endpoint for allowed/approval-required/blocked decisions.
- Added regression tests for safe, unknown, and blocked actions.

## 0.4.0 — bounded executor

- Added `/execute` with fixed safe actions (`run_tests`, `read_project_file`).
- Added approval gate and path traversal protection.
- Added local JSONL audit ledger.
- Added Side Panel button for fixed Smoke Tests that cannot recursively invoke the full suite.

## 0.5.0 — structured operations

- Added structured `/plan`, `/diff`, `/apply`, `/rollback`, and `/audit` endpoints.
- Added hash-chained audit verification.
- Added explicit approval for patch apply and rollback.
- Added fixed safe test execution, Docker Compose, CI workflow, architecture, and security docs.
- Added a goal-to-plan control in the Side Panel.

## 0.5.1 — research notes

- Added `RESEARCH_NOTES.md` with verified public sources, unknowns, and bounded next experiments.

## 0.5.2 — audit fix

- Made the `/execute` `read_project_file` secret-like filename check case-insensitive (`.lower()` on path parts), matching `/diff`/`/apply` `safe_target` behavior so files named like `Password.txt` or `Cookie` are blocked the same way.
- Added a regression test for uppercase secret-like filenames.
- Re-ran unit tests, compile checks, and live API security checks (CORS, OPTIONS gate, action policy, redaction, injection, path traversal, approval gate, audit chain).

## Audit round — 2026-10-04 18:15 ICT (recurring audit)

- Tests: 14/14 passed (13 existing + 1 new regression for case-insensitive secret-like filenames).
- Compile: passed. Live API security checks: passed — CORS rejects non-allowlisted origins (no ACAO header), OPTIONS preflight returns 403 for unknown origins, action policy blocks high-risk/evasion actions and defaults unknown actions to human approval, redaction removes emails/phones/secrets, prompt-injection and risk terms detected, path traversal blocked, approval gate holds apply/rollback, hash-chained audit ledger verified (33 entries).
- Fix applied this round: `/execute` `read_project_file` now lowercases path parts before checking `SECRET_FILE_PARTS`, matching `safe_target` in `/diff`/`/apply`, so names like `PASSWORD`, `.ENV`, `Cookie`, `Token` are blocked case-insensitively.
