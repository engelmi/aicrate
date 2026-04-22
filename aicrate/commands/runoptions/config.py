import argparse
from dataclasses import dataclass
from pathlib import Path

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
    MountedWorkspace: Path
    InternalWorkspace: Path

    def from_dict(data: dict) -> "WorkBox":
        return WorkBox(
            OCIImage=data.get("image", "quay.io/aicrate/claudebox:latest"),
            MountedWorkspace=Path(data.get("workspace", "")).expanduser().resolve(),
            InternalWorkspace=Path("/workspace").expanduser().resolve(),
        )


@dataclass
class RunConfig:

    WorkBox: WorkBox
    Skills: list[str]
    Agents: list[str]
    MCPServer: list[MCPServer]

    def from_args(args: argparse.Namespace) -> "RunConfig":
        config = {}
        if args.workspace is not None:
            config["workbox"] = {
                "workspace": args.workspace,
            }
        if args.config is not None:
            path = Path(args.config).expanduser().resolve()
            config = load_file(path)

        return RunConfig.from_dict(config)

    def from_dict(data: dict) -> "RunConfig":
        workbox = WorkBox.from_dict(data.get("workbox", {}))
        skills = data.get("skills", [])
        agents = data.get("agents", [])
        mcp = [MCPServer.from_dict(d) for d in data.get("mcp", [])]

        return RunConfig(
            WorkBox=workbox,
            Skills=skills,
            Agents=agents,
            MCPServer=mcp,
        )
