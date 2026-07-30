# InsightFlow Backend

FastAPI backend with complete authentication: register/login (JWT), Google &
GitHub OAuth, email verification, and password reset with HTML emails.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill it in (see comments inside)
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API playground.
Run tests with `pytest` (no .env needed — tests are fully isolated).

Every new terminal: `source .venv/bin/activate` first.

## Structure

```
app/
├── main.py            assembly: CORS, tables, routers — nothing else
├── core/
│   ├── config.py      ALL settings, typed, loaded from .env
│   └── security/      passwords.py (bcrypt) · tokens.py (3 JWT kinds)
├── api/
│   ├── deps.py        get_current_user — add Depends(get_current_user) to protect a route
│   └── v1/            auth.py (register/login/me/verify/reset) · oauth.py
├── services/          user_service (DB) · email_service (SMTP) · oauth_service (providers)
├── emails/            templates/*.html (content) · render.py · templates.py
├── models/            SQLAlchemy tables
├── schemas/           Pydantic shapes: user.py (identity) · auth.py (flows)
└── db/session.py      engine, SessionLocal, Base, get_db
tests/                 pytest suite — in-memory DB, fake email outbox
```

Layering rule: **router → service → model**. Routers speak HTTP and pick
status codes; services hold logic and never import FastAPI; schemas validate
the edges; secrets live only in .env.

## Where does X go? (the map)

| I want to add / change... | It goes in |
|---|---|
| An endpoint (a URL) | `api/v1/<feature>.py` |
| Request/response shape | `schemas/<feature>.py` |
| A validation rule used by ONE schema | inline `Field(...)` in that schema |
| A validation rule shared by 2+ schemas | `schemas/fields.py` |
| Business logic (DB queries, decisions) | `services/<feature>_service.py` |
| A database table | `models/<feature>.py` (+ import it in `models/__init__.py`) |
| A setting that differs per environment | `core/config.py` + `.env` |
| An error the API can return | `core/exceptions.py` |
| How errors become JSON | `api/errors.py` (already done — rarely touched) |
| "This route requires login" | add `Depends(get_current_user)` — defined in `api/deps.py` |
| Hashing / JWT logic | `core/security/` |
| What an email says | `emails/templates/<name>.html` + a function in `emails/templates.py` |
| How email is sent | `services/email_service.py` (rarely touched) |
| Custom middleware (when you write one) | `api/middleware.py` (doesn't exist yet — create when needed) |
| A constant fixed forever, one module uses it | top of that module |
| Wiring anything into the app | `main.py` |
| A test | `tests/test_<feature>.py` |

Rule of thumb when unsure: *"would this survive without a web server?"*
Yes → `core/`, `services/`, `models/`, `emails/`. No → `api/`.

## Adding a feature (the recipe)

Example: "data sources". Follow the same five steps every time:

1. `models/datasource.py` — the table (inherit `Base`, import it somewhere reachable from main)
2. `schemas/datasource.py` — `DatasourceCreate` / `DatasourceOut`
3. `services/datasource_service.py` — the logic, taking `db: Session` as first arg
4. `api/v1/datasources.py` — thin router; `include_router` it in `main.py`;
   protect routes with `current_user: User = Depends(get_current_user)`
5. `tests/test_datasources.py` — use the `client` / `db_session` / `outbox`
   fixtures from `conftest.py`; they give you a clean DB per test for free

## Gotchas (learned the hard way)

- `create_all` never ALTERs an existing table — after changing a model,
  `rm insightflow.db` (dev only; Alembic is the grown-up fix)
- `/auth/login` expects FORM fields (`username`, `password`), not JSON —
  that's the OAuth2 spec; everything else takes JSON
- OAuth users have `hashed_password = NULL` and cannot password-login
- Reset/verify links are JWTs with a `purpose` claim — token types are not
  interchangeable, and tests enforce this
