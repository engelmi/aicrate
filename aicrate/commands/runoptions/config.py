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
class BoxConfig:

    OCIImage: str
    Skills: list[str]
    Agents: list[str]

    MountedWorkspace: Path
    InternalWorkspace: Path

    Env: dict[str, str]
    EnvFile: Optional[Path]

    def from_dict(data: dict) -> "BoxConfig":
        envfile = data.get("envfile", None)
        if envfile is not None:
            envfile = Path(envfile).expanduser().resolve()

        return BoxConfig(
            OCIImage=data.get("image", "quay.io/aicrate/claudebox:latest"),
            Skills=data.get("skills", []),
            Agents=data.get("agents", []),
            MountedWorkspace=Path(data.get("workspace", "")).expanduser().resolve(),
            InternalWorkspace=Path("/workspace"),
            EnvFile=envfile,
            Env=data.get("env", {}),
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
        if args.workspace is not None:
            if "workbox" not in config:
                config["workbox"] = {}
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
