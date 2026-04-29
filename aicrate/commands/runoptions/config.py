import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from aicrate.common.file import load_file


@dataclass
class MCPServerConfig:

    OCIImage: str
    Port: int
    Env: list[tuple[str, str]]

    def from_dict(data: dict) -> "MCPServerConfig":
        return MCPServerConfig(
            OCIImage=data.get("image", ""),
            Port=data.get("port", ""),
            Env=[entry for entry in data.get("env", [])],
        )


@dataclass
class MountConfig:
    From: Path
    To: Path


@dataclass
class Ignite:
    ScriptContent: str


@dataclass
class BoxConfig:

    OCIImage: str
    Skills: list[str]
    Agents: list[str]

    MountedWorkspace: Path
    InternalWorkspace: Path

    AdditionalMounts: list[MountConfig]

    Env: dict[str, str]
    EnvFile: Optional[Path]

    Ignite: Optional[Ignite]

    def from_dict(data: dict) -> "BoxConfig":
        envfile = data.get("envfile", None)
        if envfile is not None:
            envfile = Path(envfile).expanduser().resolve()

        ignite: Optional[Ignite] = None
        ignite_script = data.get("ignite", {}).get("script", None)
        if ignite_script is not None:
            ignite = Ignite(ScriptContent=ignite_script)
        # Give preference to the ignite file over the written script
        ignite_file = data.get("ignite", {}).get("file", None)
        if ignite_file is not None:
            ignite_file_path = Path(ignite_file)
            if ignite_file_path.exists():
                with open(ignite_file_path, "r") as f:
                    ignite = Ignite(ScriptContent=f.read())

        return BoxConfig(
            OCIImage=data.get("image", "quay.io/aicrate/claudebox:latest"),
            Skills=data.get("skills", []),
            Agents=data.get("agents", []),
            MountedWorkspace=Path(data.get("workspace", "")).expanduser().resolve(),
            InternalWorkspace=Path("/workspace"),
            AdditionalMounts=[
                (
                    MountConfig(
                        Path(mount["from"]).expanduser().resolve(),
                        Path(mount["to"]).expanduser().resolve(),
                    )
                )
                for mount in data.get("mounts", [])
            ],
            EnvFile=envfile,
            Env=data.get("env", {}),
            Ignite=ignite,
        )


@dataclass
class RunConfig:

    # Config file args
    WorkBox: BoxConfig
    AgentBoxes: list[BoxConfig]
    MCPServer: list[MCPServerConfig]

    # CLI args
    Detached: bool

    def from_args(args: argparse.Namespace) -> "RunConfig":
        config = {}
        if args.config is not None:
            path = Path(args.config).expanduser().resolve()
            config = load_file(path)

        if "workbox" not in config:
            config["workbox"] = {}
        if "workspace" not in config["workbox"]:
            config["workbox"]["workspace"] = args.workspace

        workbox = BoxConfig.from_dict(config.get("workbox", {}))
        agentboxes = [
            BoxConfig.from_dict(box_config)
            for box_config in config.get("agentboxes", [])
        ]
        mcp = [MCPServerConfig.from_dict(d) for d in config.get("mcp", [])]

        return RunConfig(
            WorkBox=workbox,
            AgentBoxes=agentboxes,
            MCPServer=mcp,
            Detached=args.detached,
        )
