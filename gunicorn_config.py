import multiprocessing
import os

bind = "0.0.0.0:" + os.environ.get("PORT", "8000")
workers = 1  # Reduced to minimum for memory conservation
worker_class = "sync"
threads = 1  # Reduce to 1 thread to minimize memory usage
timeout = 600  # Increase timeout further for ML processing
max_requests = 50  # Reduce max requests to prevent memory leaks
max_requests_jitter = 5
preload_app = False  # Disable preloading to reduce memory usage
worker_tmp_dir = "/dev/shm"  # Use RAM-based temporary directory
keepalive = 60
graceful_timeout = 300
forwarded_allow_ips = '*'
limit_request_line = 0
