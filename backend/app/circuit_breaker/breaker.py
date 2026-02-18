from __future__ import annotations

import enum
import threading
import time

from app.metrics.registry import metrics_registry


class BreakerState(str, enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, *, error_threshold: int, window_seconds: int, cooldown_seconds: int) -> None:
        self.error_threshold = error_threshold
        self.window_seconds = window_seconds
        self.cooldown_seconds = cooldown_seconds
        self._state = BreakerState.CLOSED
        self._events: list[float] = []
        self._opened_at = 0.0
        self._half_open_inflight = False
        self._lock = threading.Lock()

    def _prune(self, now_ts: float) -> None:
        window_start = now_ts - self.window_seconds
        self._events = [event for event in self._events if event >= window_start]

    def is_open(self, now: float | None = None) -> bool:
        now_ts = now if now is not None else time.time()
        with self._lock:
            if self._state == BreakerState.OPEN and (now_ts - self._opened_at) >= self.cooldown_seconds:
                self._state = BreakerState.HALF_OPEN
                self._half_open_inflight = False
            return self._state == BreakerState.OPEN

    def allow_request(self, now: float | None = None) -> bool:
        now_ts = now if now is not None else time.time()
        with self._lock:
            if self._state == BreakerState.OPEN:
                if (now_ts - self._opened_at) >= self.cooldown_seconds:
                    self._state = BreakerState.HALF_OPEN
                    self._half_open_inflight = False
                else:
                    return False
            if self._state == BreakerState.HALF_OPEN:
                if self._half_open_inflight:
                    return False
                self._half_open_inflight = True
                return True
            return True

    def record_success(self) -> None:
        with self._lock:
            self._events.clear()
            self._state = BreakerState.CLOSED
            self._half_open_inflight = False
            self._opened_at = 0.0

    def record_provider_error(self, now: float | None = None) -> None:
        now_ts = now if now is not None else time.time()
        with self._lock:
            if self._state == BreakerState.HALF_OPEN:
                self._state = BreakerState.OPEN
                self._opened_at = now_ts
                self._half_open_inflight = False
                metrics_registry.inc("circuit_breaker_open_total")
                return
            self._events.append(now_ts)
            self._prune(now_ts)
            if len(self._events) >= self.error_threshold:
                self._state = BreakerState.OPEN
                self._opened_at = now_ts
                self._half_open_inflight = False
                metrics_registry.inc("circuit_breaker_open_total")
