# Production image for Averra. Build with: docker build -t averra .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AVERRA_ENV=production \
    AVERRA_DATABASE=/app/instance/averra.sqlite3

WORKDIR /app

RUN groupadd --system averra && useradd --system --gid averra --create-home averra
COPY requirements-deploy.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY averra ./averra
COPY migrations ./migrations
COPY templates ./templates
COPY static ./static
COPY app.py wsgi.py gunicorn.conf.py ./

RUN mkdir -p /app/instance && chown -R averra:averra /app
USER averra

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/ready', timeout=3)"

CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
