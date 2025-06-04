#!/usr/bin/env python
"""Fetch recent dash error logs for debugging.

This utility reads ``logs/dash_errors.log`` and prints the last
N lines. Agents can use this to quickly review the latest issues
reported by the app.
"""
from pathlib import Path
import argparse

LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "dash_errors.log"


def tail_log(lines: int = 50) -> str:
    if not LOG_FILE.exists():
        return ""
    with LOG_FILE.open("r", encoding="utf-8") as f:
        log_lines = f.readlines()
    return "".join(log_lines[-lines:])


def main():
    parser = argparse.ArgumentParser(description="Display recent dash error logs")
    parser.add_argument("-n", "--lines", type=int, default=50,
                        help="Number of lines to show")
    args = parser.parse_args()
    output = tail_log(args.lines)
    print(output)


if __name__ == "__main__":
    main()
