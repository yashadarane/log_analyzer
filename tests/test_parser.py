# tests/test_parser.py
# ---------------------------------------------------------------------------
# Unit tests for the parser module — stdlib unittest only (no pytest needed).
# Run with:  python -m unittest discover tests/ -v
# ---------------------------------------------------------------------------

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import tempfile
from pathlib import Path
from datetime import datetime

from log_analyser.parser import parse_line, stream_log_file, stream_log_directory
from log_analyser.models import LogEntry


class TestParseLine(unittest.TestCase):

    def test_valid_line(self):
        line = "2026-03-18 10:15:23 | INFO | service_a | Request completed in 120ms"
        entry = parse_line(line)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.timestamp, datetime(2026, 3, 18, 10, 15, 23))
        self.assertEqual(entry.level,   "INFO")
        self.assertEqual(entry.service, "service_a")
        self.assertEqual(entry.message, "Request completed in 120ms")

    def test_blank_line_returns_none(self):
        self.assertIsNone(parse_line(""))
        self.assertIsNone(parse_line("   "))

    def test_too_few_fields_returns_none(self):
        self.assertIsNone(parse_line("2026-03-18 10:15:23 | INFO | service_a"))

    def test_too_many_fields_returns_none(self):
        self.assertIsNone(
            parse_line("2026-03-18 10:15:23 | INFO | service_a | msg | extra")
        )

    def test_bad_timestamp_returns_none(self):
        self.assertIsNone(parse_line("BADDATE | INFO | service_a | msg"))

    def test_level_uppercased(self):
        line = "2026-03-18 10:00:00 | error | service_a | oops"
        entry = parse_line(line)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.level, "ERROR")

    def test_whitespace_stripped(self):
        line = "  2026-03-18 10:00:00  |  INFO  |  svc  |  hello world  "
        entry = parse_line(line)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.service, "svc")
        self.assertEqual(entry.message, "hello world")


class TestStreamLogFile(unittest.TestCase):

    def test_valid_file_yields_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "test.log"
            log.write_text(
                "2026-03-18 10:00:01 | INFO  | svc | msg1\n"
                "2026-03-18 10:00:02 | ERROR | svc | msg2\n"
            )
            entries = list(stream_log_file(log))
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].level, "INFO")
        self.assertEqual(entries[1].level, "ERROR")

    def test_malformed_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "bad.log"
            log.write_text(
                "COMPLETELY MALFORMED LINE\n"
                "2026-03-18 10:00:01 | INFO | svc | valid\n"
            )
            entries = list(stream_log_file(log))
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].message, "valid")

    def test_missing_file_yields_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = list(stream_log_file(Path(tmp) / "nonexistent.log"))
        self.assertEqual(entries, [])

    def test_empty_file_yields_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "empty.log"
            log.write_text("")
            entries = list(stream_log_file(log))
        self.assertEqual(entries, [])


class TestStreamLogDirectory(unittest.TestCase):

    def test_reads_all_log_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.log").write_text(
                "2026-03-18 10:00:01 | INFO | svc | m1\n"
            )
            (Path(tmp) / "b.log").write_text(
                "2026-03-18 10:00:02 | WARN | svc | m2\n"
            )
            entries = list(stream_log_directory(tmp))
        self.assertEqual(len(entries), 2)

    def test_ignores_non_log_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "notes.txt").write_text("not a log\n")
            (Path(tmp) / "app.log").write_text(
                "2026-03-18 10:00:01 | INFO | svc | ok\n"
            )
            entries = list(stream_log_directory(tmp))
        self.assertEqual(len(entries), 1)

    def test_missing_directory_raises(self):
        with self.assertRaises(FileNotFoundError):
            list(stream_log_directory("/does/not/exist/at/all"))

    def test_empty_directory_yields_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = list(stream_log_directory(tmp))
        self.assertEqual(entries, [])


if __name__ == "__main__":
    unittest.main()