# auth-backend

FastAPI authentication service providing JWT-based login, registration, password reset, and token refresh.

---

## Overview

This service implements the following endpoints:

| Method | Path                    | Handler         | Description                          |
|--------|-------------------------|-----------------|--------------------------------------|
| POST   | `/auth/register`        | `register`      | Create a new user account            |
| POST   | `/auth/login`           | `login`         | Authenticate and receive tokens      |
| GET    | `/auth/me`              | `me`            | Return the current authenticated user|
| POST   | `/auth/logout`          | `logout`        | Revoke the current refresh token     |
| POST   | `/auth/refresh`         | `refresh`       | Rotate and issue a new access token  |
| POST   | `/auth/forgot-password` | `forgotPassword` | Send a password-reset email         |
| POST   | `/auth/reset-password`  | `resetPassword` | Apply a password reset               |

### Database tables

- `users` — core account records (`User`)
- `refresh_tokens` — hashed, rotatable refresh tokens (`RefreshToken`)
- `password_resets` — single-use, hashed reset tokens (`PasswordReset`)

---

## Prerequisites

- Python 3.12+
- PostgreSQL 15+
- (Optional) Docker & Docker Compose

---

## Local setup

### 1. Clone and enter the directory

```bash
git clone <repo-url>
cd auth-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install --no-cache-dir -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your values — see the Environment Variables section below
```

### 5. Apply the database schema

Run `schema.sql` against your PostgreSQL instance:

```bash
psql "$DATABASE_URL" -f ../schema.sql
```

### 6. Start the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive docs are at `http://localhost:8000/docs`.

---

## Docker

Build and run the service in isolation:

```bash
docker build -t auth-backend .
docker run --env-file .env -p 8000:8000 auth-backend
```

Or start the full stack (backend + database + frontend) with Docker Compose from the repository root:

```bash
docker compose up --build
```

---

## Running tests

```bash
pytest
```

Test coverage includes:

- Happy-path flow: register → login → refresh → forgot-password → reset-password → logout
- Negative cases: duplicate email, weak password, password mismatch, expired/used tokens

---

## Environment variables

All variables are read from `.env` at startup. Copy `.env.example` and fill in your values.

### Database

| Variable       | Description                              | Example                                              |
|----------------|------------------------------------------|------------------------------------------------------|
| `DATABASE_URL` | SQLAlchemy-compatible PostgreSQL DSN     | `postgresql+psycopg://user:password@localhost:5432/authdb` |

### JWT

| Variable                      | Description                                                | Default  |
|-------------------------------|------------------------------------------------------------|----------|
| `JWT_SECRET_KEY`              | Secret used to sign access tokens — **change in production** | —      |
| `JWT_ALGORITHM`               | Signing algorithm                                          | `HS256`  |
| `JWT_ACCESS_TOKEN_TTL_MINUTES`| Access token lifetime in minutes                           | `15`     |

### Refresh tokens

| Variable                              | Description                                              | Default |
|---------------------------------------|----------------------------------------------------------|---------|
| `REFRESH_TOKEN_TTL_DAYS`              | Refresh token lifetime (days) without remember-me        | `7`     |
| `REFRESH_TOKEN_TTL_DAYS_REMEMBER_ME`  | Refresh token lifetime (days) with remember-me enabled   | `30`    |

### Password hashing

| Variable        | Description                               | Default |
|-----------------|-------------------------------------------|---------|
| `BCRYPT_ROUNDS` | bcrypt work factor — minimum 12 in production | `12` |

### Password reset

| Variable                    | Description                              | Default |
|-----------------------------|------------------------------------------|---------|
| `RESET_TOKEN_TTL_MINUTES`   | Password-reset token lifetime in minutes | `60`    |

### SMTP (password-reset emails)

| Variable        | Description                         | Example                    |
|-----------------|-------------------------------------|----------------------------|
| `SMTP_HOST`     | Mail server hostname                | `smtp.example.com`         |
| `SMTP_PORT`     | Mail server port                    | `587`                      |
| `SMTP_USERNAME` | SMTP authentication username        | `no-reply@example.com`     |
| `SMTP_PASSWORD` | SMTP authentication password        | —                          |
| `SMTP_FROM`     | Sender address shown in emails      | `no-reply@example.com`     |
| `SMTP_TLS`      | Enable STARTTLS (`true` / `false`)  | `true`                     |

### Rate limiting

| Variable                                 | Description                                           | Default |
|------------------------------------------|-------------------------------------------------------|---------|
| `RATE_LIMIT_LOGIN_MAX`                   | Max login attempts per window                         | `10`    |
| `RATE_LIMIT_LOGIN_WINDOW_SECONDS`        | Login rate-limit window in seconds                    | `60`    |
| `RATE_LIMIT_FORGOT_PASSWORD_MAX`         | Max forgot-password requests per window               | `5`     |
| `RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS` | Forgot-password rate-limit window in seconds       | `60`    |

### Application

| Variable       | Description                                      | Example                    |
|----------------|--------------------------------------------------|----------------------------|
| `APP_BASE_URL` | Public base URL of the frontend (used in emails) | `http://localhost:3000`    |
| `CORS_ORIGIN`  | Allowed CORS origin for the frontend             | `http://localhost:3000`    |

---

## Project structure

```
auth-backend/
├── app/
│   ├── main.py              # FastAPI application factory
│   ├── config.py            # Settings (reads .env)
│   ├── database.py          # SQLAlchemy engine and session
│   ├── auth/
│   │   ├── router.py        # Route handlers (login, register, …)
│   │   ├── service.py       # Business logic
│   │   └── schemas.py       # Pydantic request/response models
│   └── models/
│       ├── user.py          # User ORM model
│       ├── refresh_token.py # RefreshToken ORM model
│       └── password_reset.py# PasswordReset ORM model
├── tests/
│   └── test_auth.py
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## Security notes

- Passwords are hashed with **bcrypt** (`BCRYPT_ROUNDS` ≥ 12); plaintext passwords are never stored or logged.
- Refresh tokens and password-reset tokens are stored as **SHA-256 hashes**; the raw token is only ever sent to the client.
- Login failures always return `"Invalid email or password."` regardless of whether the email exists (enumeration resistance).
- Forgot-password always returns a generic 202 response regardless of whether the email is registered.
- Refresh tokens are rotated on every use and fully revoked on logout.
