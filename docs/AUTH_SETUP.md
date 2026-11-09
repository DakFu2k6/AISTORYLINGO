# Authentication setup and review

## Login methods
- Email + password (existing accounts)
- Unique username + password (new registrations)
- Google Identity Services (configured OAuth web client)

Existing accounts created before this update have no username yet and can still sign in with email. Do not infer usernames from display names because they may collide. A future profile endpoint can let existing users claim an available username.

## Google setup
1. In Google Cloud Console create an OAuth 2.0 **Web application** client.
2. Add your actual frontend origins under **Authorized JavaScript origins**, for example `http://localhost:5500` and `http://127.0.0.1:5500` (these are distinct origins).
3. Put the Web client ID in the root `.env`: `GOOGLE_CLIENT_ID=...apps.googleusercontent.com`.
4. Restart FastAPI and serve the frontend through an HTTP server, not `file://`.
5. Verify `GET http://localhost:8000/auth/config` returns a nonempty `google_client_id`.
6. If Google is blocked by extensions, browser privacy settings or network, the status area will show an error and a retry control.

Google sign-in never requires entering a Google password in this application. For an email that already has a local account, the server currently refuses automatic linking; use password login instead. This is intentional to avoid unsafe account linking.

## Backend
Start from `backend` with `uvicorn app.main:app --reload`. SQLModel creates tables and the existing database helper adds the nullable `users.username` column. Back up your database before running migrations. For production, use Alembic migrations and a DB-level unique index on username, plus distributed rate limiting and secure session-cookie design.

## Verification checklist
- Register a new user with a unique username; log out; log in with username; log out; log in with email.
- Duplicate username should be rejected. Existing email-only accounts must continue to work.
- Configure Google client ID; verify button appears; test new Google account with accepted terms.
- Verify expired nonce and reused nonce are rejected; existing local email cannot silently link to Google.
- Test password reset, admin access and navigation on mobile.

## Important
The ZIP excludes `.env`, local databases, `.git`, and generated dependency/cache directories. Keep the original `.env` privately and do not commit it to source control.
