# Averra architecture

```text
Browser / PWA (frontend/)
    │ same-origin JSON
    ▼
Flask application factory (backend/averra/)
    ├── web.py       HTML shell
    ├── api.py       health, auth, attendance, roster, reports
    ├── auth.py      credential-ready session boundary
    ├── db.py        connection lifecycle + migrations
    ├── seed.py      opt-in local demo data
    └── services/    face-recognition adapter
            │
            ▼
       SQLite + WAL (instance/averra.sqlite3)
```

The root implementation is intentionally separated into `backend/`, `frontend/`, `database/`, `data/`, and `scripts/`. Compatibility wrappers for the original prototype live under `backend/compat/`. New integrations should use `backend.averra.create_app`, `backend.averra.db`, and `backend.averra.api` directly.
