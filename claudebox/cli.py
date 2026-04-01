import os
import json
import yaml
from pathlib import Path
from typing import Sequence, Tuple
import argparse

from claudebox.version import version
from claudebox.logger import LogLevel, logger
from claudebox.common.ds import deep_merge
from claudebox.common.command import run_cmd_with_error_handler
from claudebox.systemd.quadlet import QuadletSectionContainer, QuadletSectionInstall, QuadletSectionPod, QuadletSectionUnit, QuadletContainer, QuadletPod


def parse_log_level_option(option: str) -> LogLevel:
    return LogLevel.from_string(option)


def parse_arguments(
    args: Sequence[str] = None,
) -> Tuple[argparse.Namespace, argparse.ArgumentParser]:
    parser = argparse.ArgumentParser(
        description="claudebox - containerize your AI agent",
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
    init_parser = parent_parser.add_parser(
        "run", help="Run a new claudebox"
    )
    init_parser.set_defaults(func=cli_run)

    init_parser.add_argument(
        "--config",
        "-c",
        help=(
            "Configuration of claudebox to use."
        ),
        dest="config",
        type=str,
        default="/home/mengel/projects/engelmi/claude-box/claudebox/claudebox.conf.yml",
    )
    init_parser.add_argument(
        "--workspace",
        "-w",
        help=(
            "The directory on the host which gets mounted into claudebox as workspace."
        ),
        dest="workspace",
        type=str,
        default=os.getcwd(),
    )
    init_parser.add_argument(
        "--output-dir",
        "-o",
        help=(
            "The directory to write the generated quadlet files to"
        ),
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

    logger.debug(f"Merged claudebox config for workspace {workspace_dir}:\n{json.dumps(merged_config, indent=2, sort_keys=True)}")
    
    claudebox_config = merged_config.get("claudebox", {})
    skills_config = merged_config.get("skills", {})
    agents_config = merged_config.get("agents", {})
    mcp_config = merged_config.get("mcp", {})

    pod_name=f"claudebox-{workspace_dir.name}"
    pod=QuadletPod(
        Filepath=output_dir / Path(f"{pod_name}.pod"),
        Unit=QuadletSectionUnit(
            Description=f"Pod for {pod_name}", 
            Before=[],
            After=["network.target"], 
            ),
        Pod=QuadletSectionPod(
            PodName=pod_name,
        ),
        Install=QuadletSectionInstall(
            WantedBy=[]
        )
    )

    container_name = f"claudebox-{workspace_dir.name}"

    skill_mounts: list[str] = []
    for skill in skills_config:
        name = skill.split("/")[-1].split(":")[0]
        skill_mounts.append(
            f"type=artifact,src={skill},dst=/var/oci-artifacts/skills/{name}"
        )
    agent_mounts: list[str] = []
    for agent in agents_config:
        name = agent.split("/")[-1].split(":")[0]
        agent_mounts.append(
            f"type=artifact,src={agent},dst=/var/oci-artifacts/agents/{name}"
        )
    
    volumes: list[str] = []
    volumes.append(f"{Path('~/.config/gcloud').expanduser().resolve()}:/root/.config/gcloud")
    volumes.append(f"{workspace_dir}:/workspace")

    claudebox_container = QuadletContainer(
            Filepath=output_dir / Path(f"{container_name}.container"),
            Unit=QuadletSectionUnit(
                Description=f"claudebox container {workspace_dir.name}",
                Before=[],
                After=[],
            ),
            Container=QuadletSectionContainer(
                Image=claudebox_config.get("image", ""),
                ContainerName=container_name,
                Pod=f"{pod_name}.pod",
                Exec="/sbin/init",
                Pull="never",
                SecurityLabelDisable=True,
                Mounts=[*skill_mounts, *agent_mounts],
                Volumes=volumes,
            ),
            Install=QuadletSectionInstall(
                WantedBy=[]
            )
        )

    with open(pod.Filepath, "w") as f:
        f.write(pod.serialize())
    with open(claudebox_container.Filepath, "w") as f:
        f.write(claudebox_container.serialize())
    run_cmd_with_error_handler(["systemctl", "--user", "daemon-reload"], [], "Failed to reload daemon and generate quadlet services")

