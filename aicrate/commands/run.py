import argparse
import json
from pathlib import Path

from aicrate.common.command import run_cmd_with_error_handler
from aicrate.common.ds import deep_merge
from aicrate.common.file import load_file
from aicrate.engine import run_aicrate
from aicrate.logger import logger
from aicrate.quadlet import build_from_config


def do(args: argparse.Namespace):
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
