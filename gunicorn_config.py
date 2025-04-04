import multiprocessing
import os

bind = "0.0.0.0:" + os.environ.get("PORT", "8000")
workers = int(os.environ.get("WEB_CONCURRENCY", 2))  # Adjust based on Railway's resources
worker_class = "sync"
threads = 1
timeout = 600
max_requests = 50
max_requests_jitter = 5
preload_app = False
worker_tmp_dir = "/dev/shm"
keepalive = 60
graceful_timeout = 300
forwarded_allow_ips = '*'
limit_request_line = 0
