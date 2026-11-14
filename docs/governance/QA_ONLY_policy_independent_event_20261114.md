# AA8 policy-independent-gate｜isolated real-event acceptance

This temporary unmerged Draft PR exercises the existing trusted-main read-only governance check. It is intentionally excluded from the public `_site` artifact (`docs/`).

- Baseline main: `c42f19c90f9165101369205d71931f4886ab75ae`
- Scope: existing governance intake only; no product page HTML, data, CRM, release or Runner changes.
- Negative phase: missing required PR metadata should yield a failed independent governance check.
- Positive phase: complete existing PR template with exact approved design/source/code/testing/rollback details; governance check should succeed.
- Test PR must be closed without merging. No production publication authorized.
