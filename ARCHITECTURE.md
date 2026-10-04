# Safe Browser Operator — Architecture

## Runtime flow

Goal → `/plan` → Observer (`activeTab`) → Action Policy → approval gate → bounded executor → verifier → hash-chained audit.

## Boundaries

- Browser access is user-invoked and per-domain allowlisted.
- Local Operator is analysis-only unless an explicit, approved endpoint is called.
- Fixed safe execution: `run_tests`, `read_project_file`.
- Diff is preview-only; apply/rollback require an explicit approval flag.
- Passwords, cookies, payments, gambling, CAPTCHA, anti-bot evasion, arbitrary shell and unrestricted browser actions are blocked.
