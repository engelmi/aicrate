import json
import pty
from dataclasses import dataclass
from pathlib import Path

from aicrate.commands.runoptions.config import RunConfig
from aicrate.common.command import run_cmd_with_error_handler


@dataclass
class MCPServer:

    Name: str
    Type: str
    URL: str


@dataclass
class ClaudeJSON:

    mcp_server: list[MCPServer]

    def to_config(self) -> str:
        server = {}
        for mcp in self.mcp_server:
            server[mcp.Name] = {"type": mcp.Type, "url": mcp.URL}

        return json.dumps(
            {"projects": {"/workspace": {"mcpServers": server}}},
            indent=2,
            sort_keys=True,
        )


def run_aicrate(cfg: RunConfig):
    workspace_name = cfg.WorkBox.MountedWorkspace.name

    pod_name = f"aicrate-{workspace_name}"
    create_pod_cmd = [
        "podman",
        "pod",
        "create",
        "--replace",
        "--exit-policy",
        "stop",
        "--infra-name",
        f"{pod_name}-infra",
        "--name",
        pod_name,
    ]

    box_container_name = f"aicrate-{workspace_name}"
    skill_mounts: list[str] = []
    for skill in cfg.WorkBox.Skills:
        name = skill.split("/")[-1].split(":")[0]
        skill_mounts.append(
            f"type=artifact,src={skill},dst=/var/oci-artifacts/skills/{name}"
        )
    agent_mounts: list[str] = []
    for agent in cfg.WorkBox.Agents:
        name = agent.split("/")[-1].split(":")[0]
        agent_mounts.append(
            f"type=artifact,src={agent},dst=/var/oci-artifacts/agents/{name}"
        )
    volumes: list[str] = []
    volumes.append(
        f"{Path('~/.config/gcloud').expanduser().resolve()}:/root/.config/gcloud"
    )
    volumes.append(f"{cfg.WorkBox.MountedWorkspace}:{cfg.WorkBox.InternalWorkspace}")

    create_container_cli_box = [
        "podman",
        "run",
        "--name",
        box_container_name,
        "--replace",
        "--rm",
        "--pull",
        "never",
        "-d",
        "--security-opt",
        "label=disable",
        "--pod",
        pod_name,
    ]
    for volume in volumes:
        create_container_cli_box.extend(["-v", volume])
    for skill_mount in skill_mounts:
        create_container_cli_box.extend(["--mount", skill_mount])
    for agent_mount in agent_mounts:
        create_container_cli_box.extend(["--mount", agent_mount])
    create_container_cli_box.extend([cfg.WorkBox.OCIImage, "/sbin/init"])

    # exec into aicrate container
    exec_into_cli_box_cmd = [
        "podman",
        "exec",
        "-it",
        "--workdir",
        "/workspace",
        box_container_name,
        "/bin/bash",
    ]

    mcp_servers_in_config: list[MCPServer] = []
    create_mcp_container_cmds: dict[str, list[str]] = {}
    for mcp in cfg.MCPServer:
        mcp_name = mcp.OCIImage.rsplit("/", 1)[1].split(":")[0]
        cmd = [
            "podman",
            "run",
            "--name",
            f"{mcp_name}-{workspace_name}",
            "--replace",
            "--rm",
            "--pull",
            "never",
            "-d",
            "--security-opt",
            "label=disable",
            "--pod",
            pod_name,
        ]
        for env_var in mcp.Env:
            for k, v in env_var.items():
                cmd.extend(["--env", f"{k}={v}"])
        cmd.append(mcp.OCIImage)

        create_mcp_container_cmds[mcp_name] = cmd

        mcp_servers_in_config.append(
            MCPServer(Name=mcp_name, Type="sse", URL=f"http://localhost:{mcp.Port}/sse")
        )

    run_cmd_with_error_handler(create_pod_cmd, [], "Failed to create aicrate pod")

    run_cmd_with_error_handler(
        create_container_cli_box, [], "Failed to create aicrate container"
    )
    claude_json = ClaudeJSON(mcp_servers_in_config).to_config()
    create_claude_json_cmd = [
        "podman",
        "exec",
        box_container_name,
        "sh",
        "-c",
        f"""cat > /root/.claude.json << \"EOF\"\n{claude_json}\nEOF""",
    ]
    run_cmd_with_error_handler(
        create_claude_json_cmd, [], "Failed to create initial .claude.json"
    )

    for name, cmd in create_mcp_container_cmds.items():
        run_cmd_with_error_handler(
            cmd, [], f"Failed to create MCP server container {name}"
        )

    try:
        pty.spawn(exec_into_cli_box_cmd)
    finally:
        if not cfg.Detached:
            run_cmd_with_error_handler(
                ["podman", "stop", pod_name], [], f"Failed to stop {pod_name}"
            )
            for name in create_mcp_container_cmds.keys():
                # do not break on an exception and keep stopping mcp containers
                try:
                    run_cmd_with_error_handler(
                        ["podman", "stop", f"{name}-{workspace_name}"],
                        [],
                        f"Failed to stop MCP server {name}",
                    )
                except Exception:
                    pass
