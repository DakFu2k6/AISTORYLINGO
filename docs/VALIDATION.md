# Validation — 7 November 2026

## Automated backend checks

Environment: Python 3.12; direct dependency versions are pinned in `backend/requirements.txt` and `requirements-dev.txt`. Database: temporary SQLite. Google token verifier, SMTP delivery and Gemini responses are mocked where applicable.

```text
python -m pytest -q
40 passed in 9.48s
```

Coverage includes:

- Original AI parsing/schema/retry/demo behavior and story-context continuity.
- Full learning flow, valid story choices, saving words, mixed quiz questions, mastery/XP/streak calculations and level recommendations.
- Email normalization, password policy, terms acceptance, bad credentials and throttling.
- Missing/expired/revoked sessions and denial of forged user IDs.
- Cross-user story, quiz and vocabulary access denial.
- Admin-only endpoints and role checks at the backend.
- Independent dashboard pagination with totals unaffected by the visible page.
- Single-use recovery links, changed passwords and revocation of previous sessions.
- Google verifier invocation with configured audience, nonce replay/mismatch rejection, unverified email rejection and account-email collision handling.
- Legacy SQLite user-table migration, default role preservation, unique Google-subject index and repeated migration safety.
- Malformed/non-object JSON rejection without an internal server error.

## Frontend checks

`node --check frontend/app.js` and `node --check frontend/api.js`: passed.

DOM integration smoke test used JSDOM with a running FastAPI backend and a static frontend server. It completed this flow without JavaScript errors:

```text
register → create → read → save word → quiz → progress
→ admin → menu → logout → recovery
errors: []
```

The smoke test verified session storage, API responses, rendered reader/quiz/progress/admin elements, both pagination controls, menu aria-expanded transitions, logout cleanup and the explicit recovery-not-configured message.

## Not verified in this environment

- Actual desktop/mobile browser rendering, layout overflow and touch behavior. Chromium download failed in the execution environment, so no screenshot-based or real-browser visual verification was completed.
- Actual Google sign-in with the team's OAuth project/client ID.
- Real SMTP delivery and a real inbox receiving the reset link.
- Actual Gemini generation using the team's key/quota.
- PostgreSQL integration; the automated suite used SQLite.
- Multi-worker/concurrent-load behavior and transactional idempotency for simultaneous chapter/quiz requests.

Run the manual demo checklist in `UPGRADE_GUIDE_VI.md` after configuring the team's local environment. This report does not claim those external integrations or visual checks have passed.
