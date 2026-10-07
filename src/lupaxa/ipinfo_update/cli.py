"""Command-line interface for the IPinfo Lite database updater."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from .update import (
    DEFAULT_TIMEOUT,
    UpdateError,
    resolve_database,
    resolve_token,
    update_database,
)
from .version import get_version


def _positive_timeout(value: str) -> float:
    """Parse a timeout that must be greater than zero."""
    try:
        timeout = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be a number") from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be greater than 0")
    return timeout


def build_parser() -> argparse.ArgumentParser:
    """Build the ``ipinfo-update`` argument parser."""
    parser = argparse.ArgumentParser(
        description="Download the IPinfo Lite database for local tools.",
    )
    parser.add_argument(
        "-t",
        "--token",
        default=None,
        metavar="TOKEN",
        help="IPinfo access token (default: IPINFO_TOKEN)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        metavar="PATH",
        help="Database path (default: /var/lib/ipinfo/ipinfo_lite.mmdb, or IPINFO_DATABASE)",
    )
    parser.add_argument(
        "--timeout",
        type=_positive_timeout,
        default=DEFAULT_TIMEOUT,
        metavar="SECONDS",
        help=f"HTTP timeout in seconds (default: {DEFAULT_TIMEOUT:g})",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Print nothing on success",
    )
    parser.add_argument("--version", action="version", version=get_version())
    return parser


def main(argv: list[str] | None = None) -> int:
    """Download the database and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    database = resolve_database(args.output)
    token = resolve_token(args.token)
    try:
        update_database(database, token, timeout=args.timeout)
    except UpdateError as exc:
        print(f"ipinfo-update: {exc}", file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"Updated database: {database}")
    return 0
