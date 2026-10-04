# Research Notes — Safe Browser Operator

## Verified public sources

1. Chrome `activeTab` permission
   - URL: https://developer.chrome.com/docs/extensions/develop/concepts/activeTab
   - Confirmed: temporary access is granted after an explicit user invocation and is revoked on navigation/close.
   - Design impact: prefer `activeTab` + `scripting` over broad host permissions.

2. Chrome Scripting API
   - URL: https://developer.chrome.com/docs/extensions/reference/api/scripting
   - Confirmed: script injection can use `activeTab` instead of permanent host permissions.
   - Design impact: keep injection user-invoked and per-tab.

3. Playwright Locators
   - URL: https://playwright.dev/docs/locators
   - Confirmed: role, label, text, placeholder, and test-id locators are preferred for resilient automation.
   - Design impact: avoid brittle XPath where possible and verify after actions.

4. Playwright Trace Viewer
   - URL: https://playwright.dev/docs/trace-viewer
   - Confirmed: traces can capture screenshots, snapshots, and action details for debugging.
   - Design impact: use traces on failure in test/sandbox environments only.

5. OWASP LLM01:2025 Prompt Injection
   - URL: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
   - Confirmed: external web content can carry indirect prompt injections; mitigations include privilege control, separating untrusted content, output validation, and human approval.
   - Design impact: page content is data, not instructions; keep the Action Policy outside the model.

## Unknowns / not yet verified

- A production LLM provider, OAuth scopes, and secret-manager choice are not selected.
- Chrome manual E2E coverage has not been run on a real user workstation.
- Cloud deployment, multi-user RBAC, retention, and incident-response requirements are not defined.
- No claim is made about production readiness, reliability, or commercial valuation from these notes.

## Safe next experiments

- Add deterministic extension E2E tests on a local demo page.
- Add structured-output validation for a future LLM adapter.
- Add adversarial fixtures for indirect prompt injection and secret leakage.
- Keep all experiments local and avoid credentials, payments, CAPTCHA, anti-bot evasion, gambling, deletion, and external submissions.
