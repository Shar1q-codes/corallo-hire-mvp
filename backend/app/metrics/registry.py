from __future__ import annotations

import threading
from collections import defaultdict


def _label_key(labels: dict[str, str] | None) -> tuple[tuple[str, str], ...]:
    if not labels:
        return tuple()
    return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


class MetricsRegistry:
    def __init__(self) -> None:
        self._counter: dict[str, dict[tuple[tuple[str, str], ...], float]] = defaultdict(dict)
        self._hist_sum: dict[str, dict[tuple[tuple[str, str], ...], float]] = defaultdict(dict)
        self._hist_count: dict[str, dict[tuple[tuple[str, str], ...], float]] = defaultdict(dict)
        self._lock = threading.Lock()

    def inc(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = _label_key(labels)
        with self._lock:
            self._counter[name][key] = self._counter[name].get(key, 0.0) + value

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = _label_key(labels)
        with self._lock:
            self._hist_sum[name][key] = self._hist_sum[name].get(key, 0.0) + value
            self._hist_count[name][key] = self._hist_count[name].get(key, 0.0) + 1.0

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "counter": {name: values.copy() for name, values in self._counter.items()},
                "hist_sum": {name: values.copy() for name, values in self._hist_sum.items()},
                "hist_count": {name: values.copy() for name, values in self._hist_count.items()},
            }


metrics_registry = MetricsRegistry()

