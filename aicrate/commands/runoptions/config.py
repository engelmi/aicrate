import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from aicrate.common.file import load_file


@dataclass
class MCPServer:

    OCIImage: str
    Port: int
    Env: list[tuple[str, str]]

    def from_dict(data: dict) -> "MCPServer":
        return MCPServer(
            OCIImage=data.get("image", ""),
            Port=data.get("port", ""),
            Env=[entry for entry in data.get("env", [])],
        )


@dataclass
class WorkBox:

    OCIImage: str
    Skills: list[str]
    Agents: list[str]

    MountedWorkspace: Path
    InternalWorkspace: Path

    def from_dict(data: dict) -> "WorkBox":
        return WorkBox(
            OCIImage=data.get("image", "quay.io/aicrate/claudebox:latest"),
            Skills=data.get("skills", []),
            Agents=data.get("agents", []),
            MountedWorkspace=Path(data.get("workspace", "")).expanduser().resolve(),
            InternalWorkspace=Path("/workspace"),
        )


@dataclass
class RunConfig:

    # Config file args
    WorkBox: WorkBox
    MCPServer: list[MCPServer]

    # CLI args
    Detached: bool
    EnvFile: Optional[Path]

    def from_args(args: argparse.Namespace) -> "RunConfig":
        config = {}
        if args.config is not None:
            path = Path(args.config).expanduser().resolve()
            config = load_file(path)
        if args.workspace is not None:
            if "workbox" not in config:
                config["workbox"] = {}
            config["workbox"]["workspace"] = args.workspace

        workbox = WorkBox.from_dict(config.get("workbox", {}))
        mcp = [MCPServer.from_dict(d) for d in config.get("mcp", [])]

        return RunConfig(
            WorkBox=workbox,
            MCPServer=mcp,
            Detached=args.detached,
            EnvFile=(
                None if not args.envfile else Path(args.envfile).expanduser().resolve()
            ),
        )
