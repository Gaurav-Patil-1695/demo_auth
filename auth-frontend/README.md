# auth-frontend

React + TypeScript single-page application that provides the user-facing authentication flows for the auth-starter project.

---

## Features

- Register (full name, email, password, confirm password, Terms acceptance)
- Login (email + password, remember me)
- Forgot password (sends reset link via backend)
- Reset password (token-based)
- Profile page (protected, requires valid session)
- Route guards: `<RequireAuth>` for protected routes, `<RequireGuest>` for auth-only routes
- JWT access token + httpOnly refresh token rotation
- Client-side password strength meter mirroring the server policy
- Fully accessible forms (labels, `aria-describedby`, `aria-live` banners, `aria-busy` on submit)

---

## Tech stack

| Tool | Version |
|---|---|
| React | 18 |
| TypeScript | 5 |
| Vite | 5 |
| React Router | 6 |
| Vitest | 1 |

---

## Prerequisites

- Node.js ≥ 18
- npm ≥ 9 (or compatible package manager)
- The auth-backend service running (default: `http://localhost:8000`)

---

## Setup

### 1. Install dependencies

```bash
cd auth-frontend
npm install
```

### 2. Configure environment variables

Copy the example file and edit as needed:

```bash
cp .env.example .env
```

See [Environment variables](#environment-variables) below for the full list.

### 3. Start the development server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

All requests to `/api/v1` are proxied to `VITE_API_BASE_URL` (default `http://localhost:8000`) via the Vite dev-server proxy configured in `vite.config.ts`.

---

## Available scripts

| Script | Description |
|---|---|
| `npm run dev` | Start Vite development server with HMR |
| `npm run build` | Type-check then produce an optimised production bundle in `dist/` |
| `npm run test` | Run the Vitest test suite once (no watch) |
| `npm run lint` | Run ESLint across `src/` — zero warnings allowed |

---

## Environment variables

All variables are prefixed with `VITE_` so that Vite exposes them to the browser bundle.

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000` | Base URL of the auth-backend API. In development, the Vite proxy rewrites `/api/v1` requests to this origin, so browser code never makes cross-origin calls during development. In production, set this to your deployed backend URL and ensure CORS is configured accordingly. |

### `.env.example`

```dotenv
# API base URL for the auth backend
VITE_API_BASE_URL=http://localhost:8000
```

---

## Project structure

```
auth-frontend/
├── index.html                  # HTML entry point
├── vite.config.ts              # Vite + proxy config
├── tsconfig.json               # TypeScript strict config
├── package.json
├── .env.example
└── src/
    ├── main.tsx                # React DOM root
    ├── App.tsx                 # Router + AuthContext provider
    ├── api/
    │   └── auth.ts             # Typed API client (login, register, …)
    ├── context/
    │   └── AuthContext.tsx     # Global auth state
    ├── hooks/
    │   └── useAuthForm.ts      # Controlled-form + client-side validation hook
    ├── components/
    │   ├── RequireAuth.tsx     # Redirects unauthenticated users to /login
    │   ├── RequireGuest.tsx    # Redirects authenticated users to /profile
    │   └── PasswordStrength.tsx
    ├── features/
    │   └── auth/
    │       └── pages/
    │           ├── LoginPage.tsx
    │           ├── RegisterPage.tsx
    │           ├── ForgotPasswordPage.tsx
    │           └── ResetPasswordPage.tsx
    ├── pages/
    │   └── ProfilePage.tsx
    └── styles/
        └── tokens.css          # CSS custom properties from design tokens
```

---

## API client

`src/api/auth.ts` exports the following functions, each mapping to a backend endpoint:

| Function | Method | Path |
|---|---|---|
| `login` | POST | `/api/v1/auth/login` |
| `register` | POST | `/api/v1/auth/register` |
| `forgotPassword` | POST | `/api/v1/auth/forgot-password` |
| `resetPassword` | POST | `/api/v1/auth/reset-password` |
| `me` | GET | `/api/v1/auth/me` |
| `logout` | POST | `/api/v1/auth/logout` |
| `refresh` | POST | `/api/v1/auth/refresh` |

---

## Production build

```bash
npm run build
```

The compiled output is written to `dist/`. Serve it with any static file host or reverse proxy. Set `VITE_API_BASE_URL` to your production backend URL at build time:

```bash
VITE_API_BASE_URL=https://api.example.com npm run build
```

---

## Running with Docker Compose

The repository root `docker-compose.yml` includes both the backend and a static-serving container for the frontend. From the repo root:

```bash
docker compose up --build
```

See the root `README.md` for full stack setup instructions.

---

## Linting and type-checking

```bash
# Type-check only (no emit)
npx tsc --noEmit

# Lint
npm run lint
```

The ESLint config enforces the React + hooks rules and TypeScript strict mode. Zero warnings are allowed in CI.
