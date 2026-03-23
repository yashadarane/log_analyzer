# log_analyzer/models.py
# ---------------------------------------------------------------------------
# Simple data classes that represent the entities our program works with.
# Using dataclasses keeps things clean, typed, and self-documenting.
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LogEntry:
    """One parsed line from a log file."""
    timestamp: datetime
    level: str
    service: str
    message: str


@dataclass
class AnomalyWindow:
    """A 5-minute window that exceeded the error threshold."""
    window_start: datetime
    window_end: datetime
    error_count: int


@dataclass
class SummaryMetrics:
    """Aggregated counts across all log files."""
    total_logs: int = 0
    levels: dict = field(default_factory=dict)       # {"INFO": 7000, ...}
    services: dict = field(default_factory=dict)     # {"service_a": 5000, ...}
    error_rate_per_service: dict = field(default_factory=dict)  # optional extra


@dataclass
class AnalysisResult:
    """Top-level output object — everything we want to report."""
    summary: SummaryMetrics = field(default_factory=SummaryMetrics)
    top_errors: list = field(default_factory=list)   # [{"message": ..., "count": ...}]
    anomalies: list = field(default_factory=list)    # [AnomalyWindow, ...]