# Lost & Found API

A REST API for reporting lost and found items, built for the **GDG Algiers development challenge**.

Users can:

- create an account and log in (JWT authentication)
- report **lost** or **found** items
- search and filter reports by type, category, status, location, keyword and date range, with pagination
- view the details of a report
- edit their own reports (only the creator can modify a report)
- mark their own reports as **recovered**

Interactive documentation is generated automatically at `/docs` (Swagger UI) and `/redoc`.

## Tech stack

- **FastAPI** for the web framework, with **Pydantic** for request and response validation
- **PostgreSQL** (hosted on [Neon](https://neon.tech)) accessed with raw SQL through **psycopg 3** (no ORM)
- **bcrypt** for password hashing and **PyJWT** for access tokens
- **uvicorn** as the ASGI server

## Project structure

```
app/
├── main.py            # FastAPI app: startup (creates tables), routers, /health
├── db.py              # connection per request (get_db / DbConn) and init_db()
├── schema.sql         # tables and indexes, applied automatically on startup
├── dependencies.py    # get_current_user_id / CurrentUserId (Bearer token auth)
├── core/
│   ├── config.py      # settings read from environment variables
│   └── security.py    # bcrypt hashing, JWT creation and verification
├── routers/
│   ├── auth.py        # /auth/register, /auth/login, /auth/me
│   └── items.py       # /items endpoints
└── schemas/
    ├── auth.py        # auth request/response models
    └── items.py       # item request/response models and search filters
```

## Getting started

### Requirements

- Python **3.11+** (developed with 3.13)
- A PostgreSQL database. A free [Neon](https://neon.tech) project works out of the box.

### 1. Install

```bash
git clone https://github.com/zaki-123610/lost-and-found-api.git
cd lost-and-found-api
python -m venv venv
source venv/Scripts/activate      # Windows (Git Bash / MSYS2)
# venv\Scripts\activate           # Windows (cmd / PowerShell)
# source venv/bin/activate        # Linux / macOS
pip install -r requirements.txt
```

### 2. Configure

Copy `.env.example` to `.env` and fill in the values:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | yes | PostgreSQL connection string, e.g. `postgresql://user:password@host/db?sslmode=require` |
| `JWT_SECRET_KEY` | yes | Secret used to sign tokens. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | Token lifetime in minutes (default `60`) |

The app refuses to start if a required variable is missing.

### 3. Run

```bash
uvicorn app.main:app --reload
```

The tables are created automatically on startup, so there is no migration step to run. Open **http://127.0.0.1:8000/docs** to explore and try the API.

## Authentication

1. Create an account with `POST /auth/register`.
2. Get a token with `POST /auth/login`.
3. Send the token on protected requests in the header `Authorization: Bearer <token>`.

In Swagger UI (`/docs`), click **Authorize**, paste the token (without `Bearer`), and every request will include it.

```bash
# Register
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "amine@example.com", "password": "strongpassword123"}'

# Log in and keep the token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "amine@example.com", "password": "strongpassword123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Report a lost item
curl -X POST http://127.0.0.1:8000/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "lost", "title": "Black leather wallet", "category": "wallets",
       "location": "USTHB, Bab Ezzouar", "event_date": "2026-10-18"}'

# Search (no token needed)
curl "http://127.0.0.1:8000/items?type=lost&location=bab%20ezzouar&q=wallet"
```

## Endpoints

| Method | Path | Auth | Description | Success |
|---|---|---|---|---|
| `POST` | `/auth/register` | — | Create an account | `201` |
| `POST` | `/auth/login` | — | Exchange email and password for a token | `200` |
| `GET` | `/auth/me` | token | The logged-in user | `200` |
| `POST` | `/items` | token | Report a lost or found item | `201` |
| `GET` | `/items` | — | Search and filter items (paginated) | `200` |
| `GET` | `/items/{id}` | — | Item details | `200` |
| `PATCH` | `/items/{id}` | owner | Update your own report | `200` |
| `PATCH` | `/items/{id}/recover` | owner | Mark your own report as recovered | `200` |
| `GET` | `/health` | — | Liveness check (does not touch the database) | `200` |

### `POST /auth/register`

Body: `email` (valid email, stored lowercase) and `password` (at least 8 characters, at most 72 bytes).

Returns the created user: `id`, `email`, `created_at`. The password hash is never returned.

Errors: `409` if the email is already registered, `422` for an invalid email or password.

### `POST /auth/login`

Body: `email`, `password`. Returns `{"access_token": "...", "token_type": "bearer"}`.

Errors: `401 Invalid email or password`. The same message is used for an unknown email and for a wrong password, so the endpoint cannot be used to discover registered emails.

### `GET /auth/me`

Returns the user who owns the token. Errors: `401` for a missing, invalid or expired token.

### `POST /items`

| Field | Type | Rules |
|---|---|---|
| `type` | string | `lost` or `found` |
| `title` | string | 1–120 characters |
| `description` | string, optional | up to 2000 characters |
| `category` | string | `electronics`, `documents`, `keys`, `wallets`, `bags`, `clothing`, `accessories`, `other` |
| `location` | string | 1–120 characters |
| `event_date` | date `YYYY-MM-DD` | the day it was lost or found; cannot be in the future |

The item belongs to the authenticated user and starts with `status: "open"`. Unknown fields are rejected.

Errors: `401` without a valid token, `422` for invalid fields.

Example response (`201`):

```json
{
  "id": 1,
  "user_id": 1,
  "type": "lost",
  "title": "Black leather wallet",
  "description": null,
  "category": "wallets",
  "location": "USTHB, Bab Ezzouar",
  "event_date": "2026-10-18",
  "status": "open",
  "created_at": "2026-10-19T18:30:00.000000Z",
  "updated_at": "2026-10-19T18:30:00.000000Z"
}
```

### `GET /items`

All query parameters are optional and are combined with AND. Results are sorted newest first.

| Parameter | Description |
|---|---|
| `type` | `lost` or `found` |
| `category` | one of the categories above |
| `status` | `open` or `recovered` |
| `location` | partial, case-insensitive match (`bab` matches `USTHB, Bab Ezzouar`) |
| `q` | keyword searched in title **and** description (partial, case-insensitive) |
| `date_from`, `date_to` | `event_date` range, inclusive (`YYYY-MM-DD`) |
| `page` | page number, starts at 1 (default `1`) |
| `page_size` | items per page, 1–100 (default `20`) |

Response:

```json
{ "items": [ ... ], "total": 42, "page": 1, "page_size": 20 }
```

`total` is the number of matching items across all pages.

Errors: `422` for an invalid value, or when `date_from` is after `date_to`.

### `GET /items/{id}`

Returns one item. Errors: `404 Item not found`.

### `PATCH /items/{id}`

Only the creator of the report can update it. Send only the fields you want to change: any of `type`, `title`, `description`, `category`, `location`, `event_date`, with the same rules as for creation. `description` can be set to `null` to clear it. The other fields cannot be `null`. `status` cannot be changed here; use the recover endpoint.

Errors: `400` for an empty body, `401` without a valid token, `403` if you are not the creator, `404` if the item does not exist, `422` for invalid fields.

### `PATCH /items/{id}/recover`

Only the creator can mark the item as recovered. No body is needed. It returns the updated item with `status: "recovered"`.

Errors: `401` without a valid token, `403` if you are not the creator, `404` if the item does not exist, `409` if it is already recovered.

## Errors

Errors use FastAPI's standard format:

```json
{ "detail": "You can only modify your own reports" }
```

Validation errors (`422`) list each invalid field:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "event_date"],
      "msg": "Value error, Date cannot be in the future",
      "input": "2099-01-01"
    }
  ]
}
```

| Code | Meaning in this API |
|---|---|
| `400` | The request is well formed but cannot be applied (empty update) |
| `401` | Missing, invalid or expired token; wrong login credentials |
| `403` | Authenticated, but not the creator of the report |
| `404` | The item does not exist |
| `409` | Conflict with the current state: email already registered, item already recovered |
| `422` | Invalid input (wrong type, missing field, out-of-range value) |

## Data model

- **users**: `id`, `email` (unique), `password_hash`, `created_at`
- **items**: `id`, `user_id` → users, `type` (`lost`/`found`), `title`, `description`, `category`, `location`, `event_date`, `status` (`open`/`recovered`), `created_at`, `updated_at`

The full definition, with constraints and indexes, is in [`app/schema.sql`](app/schema.sql).

## Design notes

- **Raw SQL, safely.** Values are always sent as query parameters, never formatted into SQL strings. The dynamic parts (search filters, the fields of a partial update) are assembled with `psycopg.sql`.
- **The database enforces the rules too.** It has `UNIQUE` emails, `CHECK` constraints on `type` and `status`, and a foreign key from items to users. A duplicate email is detected by the unique constraint, which avoids the race condition of checking for the email first.
- **Passwords** are hashed with bcrypt and a per-password salt. bcrypt's 72-byte limit is validated with a clear message.
- **Tokens** are signed JWTs (HS256) containing the user id and an expiry. Only HS256 is accepted when decoding them.
- **401 vs 403:** `401` means "we don't know who you are", and `403` means "we know who you are, but this report isn't yours".
- **Fixed categories** keep filtering reliable, so `phone` and `Phones` can't become two different categories.
- **One connection per request** in autocommit mode: every write is a single statement, and the connection is always closed after the request.

## Deploying on Render

1. Push the repository to GitHub.
2. On [Render](https://render.com), create a **New → Web Service** and connect the repository.
3. Use these settings:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health check path:** `/health`
4. Add the environment variables:
   - `DATABASE_URL`: your Neon connection string. Neon's **pooled** connection string is a good fit.
   - `JWT_SECRET_KEY`: a new random value, not the one from your local `.env`.
   - `PYTHON_VERSION`: optional, to pin the Python version (for example the one shown by `python --version` locally). The app needs 3.11 or newer.
5. Deploy. The API docs will be at `https://<your-service>.onrender.com/docs`.

On Render's free plan, the service sleeps after a period of inactivity, so the first request after a pause can take a while to answer.
