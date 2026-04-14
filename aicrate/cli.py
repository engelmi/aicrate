import argparse
import json
import os
from pathlib import Path
from typing import Sequence, Tuple

import yaml

from aicrate.common.command import run_cmd_with_error_handler
from aicrate.common.ds import deep_merge
from aicrate.engine import run_aicrate
from aicrate.logger import LogLevel, logger
from aicrate.systemd.quadlet import build_from_config
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
    init_parser = parent_parser.add_parser("run", help="Run a new aicrate")
    init_parser.set_defaults(func=cli_run)

    init_parser.add_argument(
        "--config",
        "-c",
        help=("Configuration of aicrate to use."),
        dest="config",
        type=str,
        default="/home/mengel/projects/engelmi/aicrate/aicrate/aicrate.conf.yml",
    )
    init_parser.add_argument(
        "--mode",
        "-m",
        help=("The mode how to run aicrate"),
        dest="mode",
        choices=["systemd", "podman"],
        default="podman",
    )

    init_parser.add_argument(
        "--workspace",
        "-w",
        help=(
            "The directory on the host which gets mounted into aicrate as workspace."
        ),
        dest="workspace",
        type=str,
        default=os.getcwd(),
    )
    init_parser.add_argument(
        "--output-dir",
        "-o",
        help=("The directory to write the generated quadlet files to"),
        dest="output_dir",
        type=str,
        default="~/.config/containers/systemd",
    )


def load_file(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"File '{path}' not found")

    with open(path, "r") as f:
        if path.suffix == ".json":
            return json.load(f)
        elif path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)

        raise NotImplementedError(f"File extension '{path.suffix}' not supported")


def cli_run(args: argparse.Namespace):
    config_file = Path(args.config)
    workspace_dir = Path(args.workspace).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    config = load_file(config_file)
    merged_config = dict()
    for key, value in config.get("default", {}).items():
        merged_config[key] = value

    if args.workspace in config:
        merged_config = deep_merge(merged_config, config.get(args.workspace, {}))

    logger.debug(
        f"Merged aicrate config for workspace {workspace_dir}:\n{json.dumps(merged_config, indent=2, sort_keys=True)}"
    )

    if args.mode == "systemd":
        pod, containers = build_from_config(merged_config, workspace_dir, output_dir)
        with open(pod.Filepath, "w") as f:
            f.write(pod.serialize())
        for container in containers:
            with open(container.Filepath, "w") as f:
                f.write(container.serialize())
        run_cmd_with_error_handler(
            ["systemctl", "--user", "daemon-reload"],
            [],
            "Failed to reload daemon and generate quadlet services",
        )
    elif args.mode == "podman":
        run_aicrate(merged_config, workspace_dir)
    else:
        raise NotImplementedError(f"Mode '{args.mode}' not implemented")
