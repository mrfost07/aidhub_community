import multiprocessing
import os

bind = "0.0.0.0:" + os.environ.get("PORT", "8000")
workers = 1  # Reduced to minimum for memory conservation
worker_class = "sync"
threads = 2
timeout = 300  # Increased timeout for ML operations
max_requests = 1000
max_requests_jitter = 50
preload_app = False  # Disable preloading to reduce memory usage
worker_tmp_dir = "/dev/shm"  # Use RAM-based temporary directory
