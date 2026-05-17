import os


bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
# Keep defaults low for Render starter instances (prevents OOM restarts).
workers = int(os.getenv('WEB_CONCURRENCY', '1'))
threads = int(os.getenv('GUNICORN_THREADS', '1'))
timeout = int(os.getenv('GUNICORN_TIMEOUT', '300'))
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', '30'))
keepalive = 5
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', '200'))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', '20'))
