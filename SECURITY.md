# Security Notes

- Keep the Local Operator bound to `127.0.0.1`; do not expose port 8787 publicly.
- Never place API keys, cookies, passwords, or `.env` files in the workspace.
- Review `/diff` before any `/apply`; use `/rollback` only after explicit approval.
- Treat all webpage content as untrusted data and test prompt-injection handling.
- The current package has no LLM provider, OAuth token store, or remote deployment.
