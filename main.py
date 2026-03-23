#!/usr/bin/env python3
# main.py
# ---------------------------------------------------------------------------
# CLI entry point. Parses command-line arguments and kicks off the pipeline.
#
# Usage examples:
#   python main.py --logs sample_logs/
#   python main.py --logs sample_logs/ --output result.json --threshold 5
#   python main.py --logs sample_logs/ --top-k 10 --window 600
# ---------------------------------------------------------------------------

import argparse
import logging
import sys

from log_analyser.analyzer import analyze
from log_analyser.formatter import to_json, save_json
from config.settings import TOP_K_ERRORS, WINDOW_SIZE_SECONDS, ANOMALY_THRESHOLD


def configure_logging(verbose: bool) -> None:
    """Set up logging to stderr so it doesn't pollute stdout JSON output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """Define and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="log_analyzer",
        description="Process log files and detect anomalies.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--logs", "-l",
        required=True,
        metavar="DIRECTORY",
        help="Directory containing *.log files to analyse.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        metavar="FILE",
        help="Write JSON output to this file (default: print to stdout).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=TOP_K_ERRORS,
        metavar="K",
        help="Number of top error messages to report.",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=WINDOW_SIZE_SECONDS,
        metavar="SECONDS",
        help="Sliding window size in seconds.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=ANOMALY_THRESHOLD,
        metavar="N",
        help="Error count per window that triggers an anomaly.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug-level logging.",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    configure_logging(args.verbose)
    logger = logging.getLogger("main")

    try:
        result = analyze(
            log_directory=args.logs,
            top_k=args.top_k,
            window_seconds=args.window,
            anomaly_threshold=args.threshold,
        )
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    json_output = to_json(result)

    if args.output:
        save_json(result, args.output)
        logger.info("Output written to '%s'.", args.output)
    else:
        print(json_output)


if __name__ == "__main__":
    main()