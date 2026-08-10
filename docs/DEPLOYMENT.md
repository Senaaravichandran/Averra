# Averra deployment runbook

## Local production-shaped run

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

Open `http://localhost:8000`. The compose file persists the SQLite database in the `averra-data` volume and disables demo seeding. This is suitable for a single-node internal deployment.

The Windows/local web install uses `requirements.txt`; the container uses `requirements-deploy.txt` so Gunicorn stays out of the cross-platform development environment.

## Credentials later

Generate a password hash without storing the password in the repository:

```powershell
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```

Set these values in your secret manager or deployment environment:

```text
AVERRA_SECRET=<long-random-session-secret>
AVERRA_AUTH_REQUIRED=true
AVERRA_ADMIN_EMAIL=<admin-email>
AVERRA_ADMIN_PASSWORD_HASH=<generated-hash>
```

Production startup intentionally fails fast if `AVERRA_SECRET` is still the local placeholder or if auth is enabled without both admin credential values.

Write endpoints are already wrapped by the authentication boundary. Until credentials are supplied, local development runs in demo mode so the UI can be evaluated without a secret.

## Health checks

- `GET /api/health` — process and recognition capability.
- `GET /api/ready` — database connectivity/readiness.
- `/api/v1/*` — versioned API alias for integrations; `/api/*` remains available for the current browser client.

The Docker healthcheck uses `/api/ready`.

## Scaling notes

Averra currently uses SQLite with WAL mode and a persistent volume, which is a good fit for one institution on one application node. For multiple web replicas, replace the repository connection layer with PostgreSQL before scaling horizontally; the API boundary and migration layout are already isolated for that next step.
