"""Production WSGI entrypoint: gunicorn wsgi:app"""

from backend.averra import create_app


app = create_app()
