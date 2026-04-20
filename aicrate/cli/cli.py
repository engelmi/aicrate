import argparse
from pathlib import Path
from typing import Sequence, Tuple

from aicrate.cli.run import add_run_parser
from aicrate.logger import LogLevel
from aicrate.version import version


def parse_log_level_option(option: str) -> LogLevel:
    return LogLevel.from_string(option)


def parse_arguments(
    args: Sequence[str] = None,
) -> Tuple[argparse.Namespace, argparse.ArgumentParser]:
    parser = argparse.ArgumentParser(
        description="aicrate - containerize your AI agent",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("--version", action="version", version=version())
    parser.add_argument(
        "--log-level",
        dest="log_level",
        default=LogLevel.INFO,
        type=parse_log_level_option,
        help="Set log level used by the application",
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        type=Path,
        help="Path to the log file. If not given, logs will be printed to stderr.",
    )

    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.required = False

    add_run_parser(subparsers)

    return parser.parse_args(args), parser
