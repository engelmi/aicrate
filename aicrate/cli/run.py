import argparse
import json
import os
from pathlib import Path

from aicrate.common.command import run_cmd_with_error_handler
from aicrate.common.ds import deep_merge
from aicrate.common.file import load_file
from aicrate.engine import run_aicrate
from aicrate.logger import logger
from aicrate.systemd.quadlet import build_from_config


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
