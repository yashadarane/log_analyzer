# log_analyzer/formatter.py
# ---------------------------------------------------------------------------
# Converts internal Python objects → the exact JSON format required.
# Keeping formatting separate from business logic is a clean architecture
# principle: if output format changes, only this file needs updating.
# ---------------------------------------------------------------------------

import json
from datetime import datetime

from log_analyser.models import AnalysisResult, AnomalyWindow
from config.settings import LOG_DATETIME_FORMAT


def _format_window(window: AnomalyWindow) -> dict:
    """Serialize a single AnomalyWindow to a dict."""
    return {
        "window_start": window.window_start.strftime(LOG_DATETIME_FORMAT),
        "window_end":   window.window_end.strftime(LOG_DATETIME_FORMAT),
        "error_count":  window.error_count,
    }


def result_to_dict(result: AnalysisResult) -> dict:
    """
    Convert AnalysisResult into a plain Python dict matching the spec:

    {
        "summary": { "total_logs": ..., "levels": {...}, "services": {...} },
        "top_errors": [ {"message": ..., "count": ...} ],
        "anomalies": [ {"window_start": ..., "window_end": ..., "error_count": ...} ]
    }
    """
    return {
        "summary": {
            "total_logs": result.summary.total_logs,
            "levels":     result.summary.levels,
            "services":   result.summary.services,
            # error_rate_per_service is an optional enhancement
            "error_rate_per_service": result.summary.error_rate_per_service,
        },
        "top_errors": result.top_errors,
        "anomalies":  [_format_window(w) for w in result.anomalies],
    }


def to_json(result: AnalysisResult, indent: int = 2) -> str:
    """Return the result as a formatted JSON string."""
    return json.dumps(result_to_dict(result), indent=indent)


def save_json(result: AnalysisResult, output_path: str) -> None:
    """Write the JSON output to a file."""
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(to_json(result))