import threading

class EmbeddingMetrics:
    """
    In-memory metrics tracking for the embedding pipeline.
    Uses thread-safe counters for metrics required by the orchestrator.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EmbeddingMetrics, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.lock = threading.Lock()
        self.total_attempts = 0
        self.successful_retries = 0
        self.failed_retries = 0
        self.cumulative_retries = 0
        self.rate_limits_429 = 0

    def record_attempt(self):
        with self.lock:
            self.total_attempts += 1

    def record_429(self):
        with self.lock:
            self.rate_limits_429 += 1

    def record_success(self, retries_used: int):
        with self.lock:
            if retries_used > 0:
                self.successful_retries += 1
                self.cumulative_retries += retries_used

    def record_failure(self, retries_used: int):
        with self.lock:
            self.failed_retries += 1
            self.cumulative_retries += retries_used

    def get_stats(self) -> dict:
        with self.lock:
            avg = self.cumulative_retries / max(1, (self.successful_retries + self.failed_retries))
            return {
                "total_attempts": self.total_attempts,
                "successful_retries": self.successful_retries,
                "failed_retries": self.failed_retries,
                "rate_limits_429": self.rate_limits_429,
                "average_retries": round(avg, 2)
            }

metrics = EmbeddingMetrics()
