#!/usr/bin/env python3
# generate_sample_logs.py
# ---------------------------------------------------------------------------
# Helper script — generates realistic *.log files in sample_logs/ for testing.
# Run once before running main.py:  python generate_sample_logs.py
# ---------------------------------------------------------------------------

import random
import os
from datetime import datetime, timedelta

OUTPUT_DIR = "sample_logs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SERVICES   = ["service_a", "service_b", "service_c", "auth_service", "db_service"]
LEVELS     = ["INFO", "WARN", "ERROR"]
LEVEL_WEIGHTS = [0.70, 0.15, 0.15]   # 70% INFO, 15% WARN, 15% ERROR

INFO_MESSAGES = [
    "Request completed in 120ms",
    "Request completed in 85ms",
    "User login successful",
    "Cache hit ratio 0.94",
    "Health check passed",
    "Config reloaded",
    "Connection pool size: 10",
]
WARN_MESSAGES = [
    "Retry attempt 1",
    "Retry attempt 2",
    "High memory usage: 82%",
    "Slow query detected: 320ms",
    "Circuit breaker half-open",
]
ERROR_MESSAGES = [
    "Timeout occurred",
    "Connection refused",
    "Null pointer exception",
    "Database unavailable",
    "Out of memory",
    "Timeout occurred",   # repeated to make it the top error
    "Timeout occurred",
    "Connection refused",
]


def random_log_line(ts: datetime) -> str:
    level = random.choices(LEVELS, LEVEL_WEIGHTS)[0]
    service = random.choice(SERVICES)
    if level == "INFO":
        msg = random.choice(INFO_MESSAGES)
    elif level == "WARN":
        msg = random.choice(WARN_MESSAGES)
    else:
        msg = random.choice(ERROR_MESSAGES)
    return f"{ts.strftime('%Y-%m-%d %H:%M:%S')} | {level} | {service} | {msg}\n"


def generate_file(filename: str, start_time: datetime, num_lines: int, burst: bool = False) -> None:
    """
    Write *num_lines* log entries to *filename*.
    If *burst* is True, inject a spike of ERRORs to trigger anomaly detection.
    """
    path = os.path.join(OUTPUT_DIR, filename)
    ts = start_time
    with open(path, "w") as fh:
        for i in range(num_lines):
            ts += timedelta(seconds=random.randint(0, 2))

            # Inject burst: many ERRORs in a 5-minute window
            if burst and 2000 <= i <= 2050:
                line = f"{ts.strftime('%Y-%m-%d %H:%M:%S')} | ERROR | service_b | Timeout occurred\n"
            else:
                line = random_log_line(ts)

            # Occasionally inject a malformed line (edge case testing)
            if random.random() < 0.002:
                fh.write("THIS LINE IS MALFORMED AND SHOULD BE SKIPPED\n")
            else:
                fh.write(line)

    print(f"  Created {path} ({num_lines} lines)")


if __name__ == "__main__":
    base = datetime(2026, 3, 18, 9, 0, 0)
    print("Generating sample log files...")
    generate_file("app_2026_03_18_1.log", base,                      num_lines=4000, burst=True)
    generate_file("app_2026_03_18_2.log", base + timedelta(hours=1), num_lines=3500)
    generate_file("app_2026_03_18_3.log", base + timedelta(hours=2), num_lines=2500)
    print("Done. Run:  python main.py --logs sample_logs/")