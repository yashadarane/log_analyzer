# log_analyzer/metrics.py
# ---------------------------------------------------------------------------
# Responsible for computing ALL summary metrics from a stream of LogEntry
# objects. Works in a single pass — no storing all entries in memory.
#
# KEY DESIGN CHOICE — Single-Pass Streaming:
#   We iterate the generator exactly once. As each entry arrives we update
#   counters immediately, then throw it away. This is O(1) memory.
# ---------------------------------------------------------------------------

from collections import Counter, defaultdict
from typing import Generator

from log_analyser.models import LogEntry, SummaryMetrics
from config.settings import TOP_K_ERRORS, ERROR_LEVELS


def compute_summary(
    entries: Generator[LogEntry, None, None],
    *,
    error_collector: list | None = None,
) -> SummaryMetrics:
    """
    Stream through *entries* once and accumulate summary counts.

    Args:
        entries:          Generator of LogEntry objects (consumed here).
        error_collector:  If provided, ERROR-level messages are appended to
                          this list so the caller can also run top-K analysis
                          without a second pass.

    Returns:
        SummaryMetrics with total counts, per-level counts, per-service counts,
        and error rate per service.
    """
    total = 0
    level_counts: Counter = Counter()
    service_counts: Counter = Counter()
    # Track errors per service separately to compute error rate
    service_errors: Counter = Counter()

    for entry in entries:
        total += 1
        level_counts[entry.level] += 1
        service_counts[entry.service] += 1

        if entry.level in ERROR_LEVELS:
            service_errors[entry.service] += 1
            if error_collector is not None:
                error_collector.append(entry.message)

    # Error rate = errors / total_for_that_service (avoid division by zero)
    error_rate_per_service = {
        svc: round(service_errors[svc] / service_counts[svc], 4)
        for svc in service_counts
    }

    return SummaryMetrics(
        total_logs=total,
        levels=dict(level_counts),
        services=dict(service_counts),
        error_rate_per_service=error_rate_per_service,
    )


def get_top_k_errors(error_messages: list[str], k: int = TOP_K_ERRORS) -> list[dict]:
    """
    Return the *k* most frequent error messages as a list of dicts.

    Args:
        error_messages: Flat list of all error message strings.
        k:              How many top results to return.

    Returns:
        List of {"message": str, "count": int} dicts, most frequent first.
    """
    counter = Counter(error_messages)
    return [
        {"message": msg, "count": cnt}
        for msg, cnt in counter.most_common(k)
    ]