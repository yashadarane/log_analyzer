# log_analyzer/analyzer.py
# ---------------------------------------------------------------------------
# High-level orchestrator. This is the only module that imports from every
# other module. main.py and tests talk to THIS module — they don't touch the
# internals of parser/metrics/anomaly directly.
#
# Single-pass strategy:
#   We cannot iterate the generator twice (generators are exhausted after one
#   pass). So we collect error timestamps and messages WHILE computing
#   summary metrics, then use those collected lists afterwards.
# ---------------------------------------------------------------------------

import logging
from datetime import datetime

from log_analyser.models import AnalysisResult, SummaryMetrics
from log_analyser.parser import stream_log_directory
from log_analyser.metrics import compute_summary, get_top_k_errors
from log_analyser.anomaly import detect_anomalies
from config.settings import ERROR_LEVELS, TOP_K_ERRORS, WINDOW_SIZE_SECONDS, ANOMALY_THRESHOLD

logger = logging.getLogger(__name__)


def _stream_with_error_collection(directory: str, error_messages: list, error_timestamps: list):
    """
    Thin wrapper generator that taps into the log stream to collect ERROR data
    as entries flow through — without breaking the single-pass guarantee.

    Yields LogEntry objects (minus ERROR ones, which are tapped here).
    Actually yields ALL entries; side-effects fill the error lists.
    """
    for entry in stream_log_directory(directory):
        if entry.level in ERROR_LEVELS:
            error_messages.append(entry.message)
            error_timestamps.append(entry.timestamp)
        yield entry


def analyze(
    log_directory: str,
    *,
    top_k: int = TOP_K_ERRORS,
    window_seconds: int = WINDOW_SIZE_SECONDS,
    anomaly_threshold: int = ANOMALY_THRESHOLD,
) -> AnalysisResult:
    """
    Run the full analysis pipeline on *log_directory*.

    Steps:
      1. Stream all logs, computing summary metrics in one pass.
         As a side-effect, collect ERROR messages + timestamps.
      2. Compute top-K error messages from the collected list.
      3. Sort error timestamps and run anomaly detection.

    Args:
        log_directory:     Path to folder containing *.log files.
        top_k:             How many top error messages to report.
        window_seconds:    Sliding window size in seconds.
        anomaly_threshold: Error count that triggers an anomaly.

    Returns:
        AnalysisResult ready to be serialised to JSON.
    """
    error_messages: list[str] = []
    error_timestamps: list[datetime] = []

    logger.info("Starting analysis on directory: %s", log_directory)

    # --- Pass 1: streaming summary (error lists filled as side-effects) ---
    tapped_stream = _stream_with_error_collection(
        log_directory, error_messages, error_timestamps
    )
    summary: SummaryMetrics = compute_summary(tapped_stream)

    # --- Pass 2 (in-memory): top-K from already-collected list ------------
    top_errors = get_top_k_errors(error_messages, k=top_k)

    # --- Pass 3 (in-memory): anomaly detection ----------------------------
    error_timestamps.sort()
    anomalies = detect_anomalies(
        error_timestamps,
        window_seconds=window_seconds,
        threshold=anomaly_threshold,
    )

    logger.info(
        "Analysis complete — %d logs, %d anomalies detected.",
        summary.total_logs, len(anomalies),
    )

    return AnalysisResult(
        summary=summary,
        top_errors=top_errors,
        anomalies=anomalies,
    )