import argparse
from dataclasses import asdict
from pathlib import Path

from aicrate.commands.runoptions import config, engine, quadlet
from aicrate.common.command import run_cmd_with_error_handler
from aicrate.logger import logger


def run(args: argparse.Namespace):
    cfg = config.RunConfig.from_args(args)
    logger.debug(f"Using config:\n{asdict(cfg)}")

    if args.mode == "systemd":
        output_dir = Path(args.output_dir).expanduser().resolve()
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        pod, containers = quadlet.build_from_config(cfg, output_dir)
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
        engine.run_aicrate(cfg, detached=args.detached)
    else:
        raise NotImplementedError(f"Mode '{args.mode}' not implemented")
