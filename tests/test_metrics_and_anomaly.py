# tests/test_metrics_and_anomaly.py
# ---------------------------------------------------------------------------
# Unit tests for metrics and anomaly modules — stdlib unittest only.
# Run with:  python -m unittest discover tests/ -v
# ---------------------------------------------------------------------------

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from datetime import datetime

from log_analyser.models import LogEntry
from log_analyser.metrics import compute_summary, get_top_k_errors
from log_analyser.anomaly import detect_anomalies


def _make_entry(level="INFO", service="svc", message="msg",
                ts="2026-03-18 10:00:00") -> LogEntry:
    return LogEntry(
        timestamp=datetime.strptime(ts, "%Y-%m-%d %H:%M:%S"),
        level=level,
        service=service,
        message=message,
    )


class TestComputeSummary(unittest.TestCase):

    def test_counts_correctly(self):
        entries = iter([
            _make_entry("INFO",  "svc_a"),
            _make_entry("ERROR", "svc_a"),
            _make_entry("WARN",  "svc_b"),
        ])
        summary = compute_summary(entries)
        self.assertEqual(summary.total_logs, 3)
        self.assertEqual(summary.levels,   {"INFO": 1, "ERROR": 1, "WARN": 1})
        self.assertEqual(summary.services, {"svc_a": 2, "svc_b": 1})

    def test_error_rate(self):
        entries = iter([
            _make_entry("ERROR", "svc_a"),
            _make_entry("INFO",  "svc_a"),
        ])
        summary = compute_summary(entries)
        self.assertEqual(summary.error_rate_per_service["svc_a"], 0.5)

    def test_empty_stream(self):
        summary = compute_summary(iter([]))
        self.assertEqual(summary.total_logs, 0)
        self.assertEqual(summary.levels, {})

    def test_error_collector_populated(self):
        collector = []
        entries = iter([
            _make_entry("ERROR", message="boom"),
            _make_entry("INFO",  message="ok"),
        ])
        compute_summary(entries, error_collector=collector)
        self.assertEqual(collector, ["boom"])


class TestGetTopKErrors(unittest.TestCase):

    def test_returns_most_frequent(self):
        msgs = ["timeout", "timeout", "timeout", "oom", "oom", "crash"]
        result = get_top_k_errors(msgs, k=2)
        self.assertEqual(result[0], {"message": "timeout", "count": 3})
        self.assertEqual(result[1], {"message": "oom",     "count": 2})

    def test_k_larger_than_unique(self):
        msgs = ["a", "a", "b"]
        result = get_top_k_errors(msgs, k=10)
        self.assertEqual(len(result), 2)

    def test_empty_list(self):
        self.assertEqual(get_top_k_errors([]), [])


class TestDetectAnomalies(unittest.TestCase):

    def _ts(self, h=10, m=0, s=0):
        return datetime(2026, 3, 18, h, m, s)

    def test_no_errors_returns_empty(self):
        self.assertEqual(detect_anomalies([]), [])

    def test_below_threshold_no_anomaly(self):
        ts_list = [self._ts(10, 0, i) for i in range(5)]
        result = detect_anomalies(ts_list, threshold=10)
        self.assertEqual(result, [])

    def test_above_threshold_returns_anomaly(self):
        ts_list = [self._ts(10, 0, i) for i in range(15)]
        result = detect_anomalies(ts_list, window_seconds=300, threshold=10)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].error_count, 15)

    def test_multiple_windows(self):
        window1 = [self._ts(10, 0, i) for i in range(12)]
        window2 = [self._ts(10, 10, i) for i in range(11)]
        result = detect_anomalies(sorted(window1 + window2), threshold=10)
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()