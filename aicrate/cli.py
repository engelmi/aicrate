import argparse
import os
from pathlib import Path
from typing import Sequence, Tuple

from aicrate.commands import run
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


def add_run_parser(parent_parser: argparse._SubParsersAction):
    run_parser = parent_parser.add_parser("run", help="Run a new aicrate")
    run_parser.set_defaults(func=run.do)

    run_parser.add_argument(
        "--config",
        "-c",
        help=("Configuration of aicrate to use."),
        dest="config",
        type=str,
        default="/home/mengel/projects/engelmi/aicrate/aicrate/aicrate.conf.yml",
    )
    run_parser.add_argument(
        "--mode",
        "-m",
        help=("The mode how to run aicrate"),
        dest="mode",
        choices=["systemd", "podman"],
        default="podman",
    )

    run_parser.add_argument(
        "--workspace",
        "-w",
        help=(
            "The directory on the host which gets mounted into aicrate as workspace."
        ),
        dest="workspace",
        type=str,
        default=os.getcwd(),
    )
    run_parser.add_argument(
        "--output-dir",
        "-o",
        help=("The directory to write the generated quadlet files to"),
        dest="output_dir",
        type=str,
        default="~/.config/containers/systemd",
    )
