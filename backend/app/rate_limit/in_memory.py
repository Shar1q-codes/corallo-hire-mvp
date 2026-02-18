from __future__ import annotations

import threading
import time


class InMemoryTokenBucket:
    def __init__(self, capacity: int, refill_per_minute: int) -> None:
        self.capacity = float(capacity)
        self.refill_per_second = float(refill_per_minute) / 60.0
        self._state: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        now_ts = now if now is not None else time.time()
        with self._lock:
            tokens, last_ts = self._state.get(key, (self.capacity, now_ts))
            elapsed = max(0.0, now_ts - last_ts)
            refilled = min(self.capacity, tokens + elapsed * self.refill_per_second)
            if refilled < 1.0:
                self._state[key] = (refilled, now_ts)
                return False
            self._state[key] = (refilled - 1.0, now_ts)
            return True

