# Averra architecture

```text
Browser / PWA
    │ same-origin JSON
    ▼
Flask application factory (averra/)
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

The root `app.py`, `database.py`, `config.py`, and `seed.py` files are compatibility entrypoints for the original prototype. New integrations should use `averra.create_app`, `averra.db`, and `averra.api` directly.

