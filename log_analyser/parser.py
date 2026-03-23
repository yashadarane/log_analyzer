# log_analyzer/parser.py
# ---------------------------------------------------------------------------
# Responsible for ONE thing only: turning raw log lines into LogEntry objects.
#
# KEY DESIGN CHOICE — Generator Pattern:
#   Instead of reading the whole file into a list (which would crash for huge
#   files), we use Python generators (yield). This means we hand back one
#   entry at a time, so memory usage stays constant regardless of file size.
# ---------------------------------------------------------------------------

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Generator

from log_analyser.models import LogEntry
from config.settings import (
    LOG_DATETIME_FORMAT,
    LOG_SEPARATOR,
    EXPECTED_FIELD_COUNT,
)

# Module-level logger — good practice: each module has its own logger.
logger = logging.getLogger(__name__)


def parse_line(line: str, source_file: str = "") -> LogEntry | None:
    """
    Parse a single log line into a LogEntry.

    Returns None (and logs a warning) if the line is malformed so that
    the rest of processing can continue uninterrupted.

    Args:
        line:        Raw text from the log file.
        source_file: File name — used only for error messages.

    Returns:
        LogEntry on success, None on failure.
    """
    line = line.strip()
    if not line:
        return None  # blank line — silently skip

    parts = line.split(LOG_SEPARATOR)
    if len(parts) != EXPECTED_FIELD_COUNT:
        logger.warning(
            "Malformed line (expected %d fields, got %d) in '%s': %r",
            EXPECTED_FIELD_COUNT, len(parts), source_file, line,
        )
        return None

    raw_timestamp, level, service, message = (p.strip() for p in parts)

    try:
        timestamp = datetime.strptime(raw_timestamp, LOG_DATETIME_FORMAT)
    except ValueError:
        logger.warning(
            "Bad timestamp '%s' in '%s': %r",
            raw_timestamp, source_file, line,
        )
        return None

    return LogEntry(
        timestamp=timestamp,
        level=level.upper(),
        service=service,
        message=message,
    )


def stream_log_file(filepath: Path) -> Generator[LogEntry, None, None]:
    """
    Yield LogEntry objects from a single file, one at a time.

    Using a generator means we never hold the entire file in memory.
    'with open(...)' ensures the file handle is always closed, even on error.

    Args:
        filepath: Path object pointing to the log file.

    Yields:
        LogEntry for every valid line.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:                          # iterates line by line — O(1) memory
                entry = parse_line(line, source_file=str(filepath))
                if entry is not None:
                    yield entry
    except OSError as exc:
        logger.error("Cannot open file '%s': %s", filepath, exc)


def stream_log_directory(directory: str) -> Generator[LogEntry, None, None]:
    """
    Yield LogEntry objects from every *.log file found in *directory*.

    Walks the directory once, then delegates to stream_log_file for each file.
    This keeps the function simple and the memory footprint flat.

    Args:
        directory: Path to the folder containing log files.

    Yields:
        LogEntry objects from all files, in file-system order.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    log_dir = Path(directory)
    if not log_dir.is_dir():
        raise FileNotFoundError(f"Log directory not found: '{directory}'")

    log_files = sorted(log_dir.glob("*.log"))        # sorted for deterministic order
    if not log_files:
        logger.warning("No *.log files found in '%s'.", directory)
        return

    for filepath in log_files:
        logger.info("Processing file: %s", filepath.name)
        yield from stream_log_file(filepath)