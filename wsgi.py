"""Production WSGI entrypoint: gunicorn wsgi:app"""

from averra import create_app


app = create_app()
