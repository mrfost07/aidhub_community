import multiprocessing
import os

bind = "0.0.0.0:" + os.environ.get("PORT", "8000")
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
worker_class = "sync"
threads = 2
timeout = 600
max_requests = 1000
max_requests_jitter = 50
preload_app = True
worker_tmp_dir = "/tmp"
keepalive = 5
graceful_timeout = 300
forwarded_allow_ips = '*'
limit_request_line = 0
