# config/settings.py
# ---------------------------------------------------------------------------
# Central configuration — change values here, NOT inside business logic.
# ---------------------------------------------------------------------------

# Sliding-window size in seconds (5 minutes = 300 seconds)
WINDOW_SIZE_SECONDS: int = 300

# If ERROR count in a window exceeds this value, the window is an anomaly
ANOMALY_THRESHOLD: int = 10

# Number of top error messages to report
TOP_K_ERRORS: int = 5

# Expected log line format
LOG_DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# Field separator used in each log line
LOG_SEPARATOR: str = " | "

# Number of expected fields per log line
EXPECTED_FIELD_COUNT: int = 4

# Log levels recognised as error-level
ERROR_LEVELS: set = {"ERROR"}