# InsightFlow Backend

A FastAPI backend with a complete, production-shaped authentication system:
password login with JWTs, Google and GitHub OAuth, email verification, and
password reset via styled HTML emails — covered end to end by a 23-test suite.

Built as a learning project, structured like a professional one.

---

## Features

- **Register / login** — bcrypt-hashed passwords, JWT access tokens (30 min)
- **Google & GitHub sign-in** — full OAuth 2.0 authorization-code flow;
  OAuth accounts coexist with password accounts in one `users` table
- **Email verification** — signup sends a confirmation link; password reset
  is gated on a verified address
- **Password reset** — short-lived, purpose-tagged token emailed as a styled
  HTML message (with plain-text fallback)
- **Protected endpoints** — one dependency (`get_current_user`) guards any route
- **Centralized error catalog** — every user-facing error is a class with its
  status code; one handler renders them all
- **Structured logging** — loguru-rendered, level-filtered, module-tagged
- **Quality gates** — ruff lint + format and hygiene checks run on every
  commit via pre-commit hooks

## Tech stack

| Concern | Choice | Why |
|---|---|---|
| Web framework | FastAPI | validation, docs, and DI driven by type hints |
| ORM | SQLAlchemy | database-agnostic; SQLite in dev, Postgres-ready |
| Validation | Pydantic v2 | schemas double as request/response contracts |
| Auth tokens | PyJWT | small, maintained; HS256 signing |
| Password hashing | bcrypt | slow by design, industry standard |
| Email | smtplib + Gmail SMTP | zero-dependency dev sending; swap later |
| Logging | loguru (behind stdlib `logging`) | pretty output, zero app coupling |
| Tests | pytest + TestClient | in-memory DB per test, fake email outbox |
| Lint/format | ruff + pre-commit | one fast tool, enforced at commit time |

---

## Getting started

### 1. Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

> Every new terminal needs `source .venv/bin/activate` first. If `uvicorn`
> or `pip` is "command not found", this is why.

### 2. Configure

```bash
cp .env.example .env
```

Then fill in `.env`. What each value is and where to get it:

| Variable | What it is | Where to get it |
|---|---|---|
| `SECRET_KEY` | signs every JWT — treat like a password | `openssl rand -hex 32` |
| `GOOGLE_CLIENT_ID/SECRET` | Google OAuth app credentials | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → OAuth client (Web); register redirect URI `http://127.0.0.1:8000/auth/google/callback` |
| `GITHUB_CLIENT_ID/SECRET` | GitHub OAuth app credentials | GitHub → Settings → Developer settings → OAuth Apps; callback URL `http://127.0.0.1:8000/auth/github/callback` |
| `SMTP_USER/PASSWORD` | Gmail address + **App Password** (not your real password) | [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requires 2FA) |
| `FRONTEND_URL` / `BACKEND_URL` | where redirects and email links point | defaults fit local dev |
| `DATABASE_URL` | SQLAlchemy connection string | default SQLite file; `postgresql://...` in production |
| `LOG_LEVEL` | minimum level shown | `INFO` (dev) / `WARNING` (prod) |

**Everything works without OAuth/SMTP configured**: OAuth buttons will fail
politely, and emails fall back to being printed in the server log — the
reset/verify flows stay fully testable.

### 3. Run

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- **Interactive docs: http://127.0.0.1:8000/docs** — register a user, click
  *Authorize*, and exercise every endpoint from the browser
- Tests: `pytest` (needs no `.env`, touches no real database or email)

---

## API overview

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/register` | – | create account (JSON); sends verification email |
| POST | `/auth/login` | – | **form fields** `username` + `password` → JWT |
| GET | `/auth/me` | Bearer | current user |
| GET | `/auth/verify-email?token=` | – | email link target; flips `is_verified` |
| POST | `/auth/forgot-password` | – | emails reset link (verified users only) |
| POST | `/auth/reset-password` | – | token + new password → password updated |
| GET | `/auth/google/login` · `/auth/github/login` | – | redirect into OAuth flow |
| GET | `/auth/google/callback` · `/auth/github/callback` | – | provider redirects back; issues our JWT |
| GET | `/health` | – | liveness check |

### How auth works (the five flows)

1. **Register** — validate (Pydantic) → duplicate check → bcrypt hash → insert
   (unverified) → verification email sent as a background task
2. **Login** — find user → reject OAuth-only accounts (`hashed_password` is
   NULL) → bcrypt compare → signed JWT `{sub: email, exp: +30min}`
3. **Protected request** — `Authorization: Bearer <jwt>` → signature + expiry
   verified → user loaded → endpoint runs (else 401)
4. **OAuth** — redirect to provider → user consents there → provider calls
   back with a one-time code → code exchanged server-side for a verified
   email → find-or-create user → same JWT as flow 2
5. **Reset / verify links** — purpose-tagged short-lived JWTs (`password-reset`,
   `email-verify`) emailed to the user; token types are **not**
   interchangeable and tests enforce it

---

## Architecture

```
app/
├── main.py            assembly only: middleware, error handler, routers
├── core/              would survive without a web server
│   ├── config.py      every setting, typed, loaded from .env
│   ├── exceptions.py  error catalog: each error = class + status + message
│   ├── logging.py     loguru setup behind stdlib logging
│   └── security/      passwords.py (bcrypt) · tokens.py (3 JWT kinds)
├── api/               the HTTP layer
│   ├── deps.py        get_current_user (route guard)
│   ├── errors.py      AppError → JSON response
│   └── v1/            endpoints: auth.py · oauth.py
├── services/          business logic — never imports FastAPI
│   ├── user_service.py    create/find/authenticate/set_password
│   ├── email_service.py   SMTP transport (+ dev fallback to log)
│   └── oauth_service.py   Google/GitHub API calls; raises OAuthError
├── emails/            what emails say (vs services/ = how they're sent)
│   ├── templates/*.html   content with $placeholders
│   ├── render.py          template loader
│   └── templates.py       one function per email → (subject, text, html)
├── models/            SQLAlchemy tables (registered via models/__init__.py)
├── schemas/           Pydantic contracts
│   ├── user.py · auth.py  request/response shapes
│   └── fields.py          shared validation vocabulary (e.g. Password)
└── db/session.py      engine · SessionLocal · Base · get_db dependency
tests/                 conftest.py (isolated DB + email outbox) · test_auth.py
```

**The layering rule:** `router → service → model`. Routers speak HTTP and
choose status codes; services hold logic and never import FastAPI; schemas
validate at the edges; every environment-dependent value flows through
`core/config.py`; secrets exist only in `.env` (git-ignored).

**Request lifecycle:** uvicorn → CORS middleware → router matches → Pydantic
validates the body against a schema → `Depends()` supplies a DB session (and
the current user, if guarded) → service does the work → response model goes
out; any raised `AppError` is turned into JSON by the single handler.

### Where does X go? (the map)

Every row shows the rule **and** a live example already in this codebase —
open the example file to see the pattern before adding your own.

**Everyday rows (you'll use these constantly):**

| I want to add / change... | It goes in | Live example |
|---|---|---|
| An endpoint (a URL) | `api/v1/<feature>.py` | `POST /register` in `api/v1/auth.py` |
| Request/response shape | `schemas/<feature>.py` | `UserCreate` in `schemas/user.py` |
| Business logic (DB queries, decisions) | `services/<feature>_service.py` | `authenticate()` in `services/user_service.py` |
| A database table | `models/<feature>.py` + import in `models/__init__.py` | `User` in `models/user.py` |
| A test | `tests/test_<feature>.py` | `test_login_returns_token` in `tests/test_auth.py` |
| "This route requires login" | one parameter: `Depends(get_current_user)` | `read_me()` in `api/v1/auth.py` |

**Validation rows:**

| Rule scope | It goes in | Live example |
|---|---|---|
| Used by ONE schema | inline `Field(...)` in that schema | — (none yet; e.g. `bio: str = Field(max_length=500)`) |
| Shared by 2+ schemas | a named type in `schemas/fields.py` | `Password` (used by register **and** reset) |
| Cross-field logic | `@model_validator` in the schema class | — (none yet; e.g. `start < end`) |
| Needs the database ("email taken") | NOT validation → service/router | duplicate check in `register()` |

**Occasional rows (touched rarely, but this is where):**

| I want to add / change... | It goes in | Live example |
|---|---|---|
| A setting that differs per environment | `core/config.py` + `.env` | `DATABASE_URL` |
| An error the API can return | a class in `core/exceptions.py` | `EmailAlreadyRegistered` |
| Hashing / JWT logic | `core/security/` | `create_reset_token` in `tokens.py` |
| What an email says | `emails/templates/<name>.html` + a function in `emails/templates.py` | `password_reset.html` |
| A forever-fixed, single-module constant | top of that module | `PURPOSE_EMAIL_VERIFY` in `tokens.py` |
| Custom middleware (first one ever) | `api/middleware.py` — create it then | — |
| Wiring anything into the app | `main.py` | `app.add_exception_handler(...)` |

Tiebreaker when a new thing fits no row: *"would this survive without a web
server?"* Yes → `core/` / `services/` / `models/` / `emails/`. No → `api/`.

### Adding a feature (the recipe)

Example: "data sources". Same five steps every time:

1. `models/datasource.py` — the table; add its import to `models/__init__.py`
2. `schemas/datasource.py` — `DatasourceCreate` / `DatasourceOut`
3. `services/datasource_service.py` — the logic, `db: Session` as first arg
4. `api/v1/datasources.py` — thin router; `include_router` it in `main.py`;
   guard routes with `current_user: User = Depends(get_current_user)`
5. `tests/test_datasources.py` — the `client` / `db_session` / `outbox`
   fixtures give you an isolated environment for free

---

## Development workflow

```bash
pytest                        # the safety net — run before and after changes
ruff check app tests --fix    # lint (also runs on every commit)
ruff format app tests         # format (also runs on every commit)
```

Commits are guarded by pre-commit hooks (`.pre-commit-config.yaml`): ruff
lint + format, whitespace/EOF fixes, YAML check, large-file and private-key
detection. If a hook modifies files, the commit **stops** — `git add -A` and
commit again. Hooks deliberately don't run tests; that's your job before
pushing.

### Debugging notes

- Auth events (logins, failures, verifications, resets, OAuth) are logged;
  failed logins log at WARNING so attack patterns are filterable
- Without SMTP configured, emails print to the server log — copy reset/verify
  links straight from there
- Inspect the dev database: `sqlite3 insightflow.db "SELECT * FROM users;"`

## Gotchas (learned the hard way)

- `create_all` never ALTERs an existing table — after changing a model:
  `rm insightflow.db` (dev only; Alembic is the grown-up fix, see below)
- `/auth/login` expects **form fields** (`username`, `password`), not JSON —
  that's the OAuth2 password-flow spec; every other endpoint takes JSON
- OAuth users have `hashed_password = NULL` and cannot password-login;
  they're auto-verified (the provider already verified the email)
- A login token cannot be used as a reset/verify link or vice versa — the
  `purpose` claim is checked, and tests will catch any regression
- Changing `SECRET_KEY` invalidates every outstanding token (by design)

## Roadmap / known gaps

- **Alembic migrations** — replace the `rm insightflow.db` dance
- **CI** — run pytest + ruff on every push (GitHub Actions)
- **Resend-verification endpoint** — for users who lose the email
- **Rate limiting** on `/auth/login`
- Refresh tokens; httpOnly-cookie storage on the frontend; error `code`
  field for machine-readable errors
