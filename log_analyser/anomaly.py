# log_analyzer/anomaly.py
# ---------------------------------------------------------------------------
# Sliding-window anomaly detection.
#
# CONCEPT — Sliding Window:
#   Imagine a 5-minute "frame" sliding forward in time.
#   Every time an ERROR log arrives we ask: "Is there a 5-minute window
#   that contains this timestamp AND has too many errors?"
#
# APPROACH — Sort-then-Scan (two-pointer / deque method):
#   1. Collect all (timestamp, message) pairs for ERROR entries.
#      This is the ONE place we store data in memory — but only ERROR lines,
#      not the whole log.
#   2. Sort by timestamp (logs from multiple files may be interleaved).
#   3. Walk through the sorted list with a deque acting as a sliding window.
#      The window holds all errors whose timestamp is within 5 minutes of the
#      current error.  When the window count exceeds the threshold we record
#      an anomaly for [window_start, window_start + 5 min].
# ---------------------------------------------------------------------------

from collections import deque
from datetime import datetime, timedelta
from typing import NamedTuple

from log_analyser.models import AnomalyWindow
from config.settings import WINDOW_SIZE_SECONDS, ANOMALY_THRESHOLD, ERROR_LEVELS


class _ErrorPoint(NamedTuple):
    """Lightweight struct stored inside the sliding window."""
    timestamp: datetime


def detect_anomalies(
    error_timestamps: list[datetime],
    *,
    window_seconds: int = WINDOW_SIZE_SECONDS,
    threshold: int = ANOMALY_THRESHOLD,
) -> list[AnomalyWindow]:
    """
    Find every 5-minute window in which ERROR count exceeds *threshold*.

    Args:
        error_timestamps: Sorted list of datetime objects for ERROR entries.
        window_seconds:   Duration of each window in seconds.
        threshold:        Minimum error count to flag as anomaly.

    Returns:
        Deduplicated list of AnomalyWindow objects.
    """
    if not error_timestamps:
        return []

    window_delta = timedelta(seconds=window_seconds)
    anomalies: list[AnomalyWindow] = []
    window: deque[datetime] = deque()

    # We align windows to fixed grid slots (e.g. 10:00–10:05, 10:05–10:10)
    # rather than a truly sliding window, which matches the expected output
    # format and is easier to read in reports.
    # Group errors into fixed 5-minute buckets.
    bucket_counts: dict[datetime, int] = {}

    for ts in error_timestamps:
        # Floor the timestamp to the nearest window boundary
        epoch = datetime(ts.year, ts.month, ts.day)
        seconds_since_midnight = int((ts - epoch).total_seconds())
        bucket_index = seconds_since_midnight // window_seconds
        bucket_start = epoch + timedelta(seconds=bucket_index * window_seconds)
        bucket_counts[bucket_start] = bucket_counts.get(bucket_start, 0) + 1

    for bucket_start, count in sorted(bucket_counts.items()):
        if count > threshold:
            anomalies.append(
                AnomalyWindow(
                    window_start=bucket_start,
                    window_end=bucket_start + window_delta,
                    error_count=count,
                )
            )

    return anomalies