import json
import pty
from dataclasses import dataclass

import aicrate.engine.podman as engine
from aicrate.commands.runoptions.config import BoxConfig, MCPServerConfig, RunConfig
from aicrate.common.command import run_cmd_with_error_handler
from aicrate.logger import logger


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


def assemble_create_pod_cmd(workspace_name: str) -> tuple[str, list[str]]:
    pod_name = f"aicrate-{workspace_name}"

    return (
        pod_name,
        [
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
        ],
    )


def assemble_run_box_cmd(
    box_name: str, box: BoxConfig, parent_pod_name: str
) -> tuple[str, list[str]]:
    box_container_name = f"aicrate-{box_name}"
    skill_mounts: list[str] = []
    for skill in box.Skills:
        name = skill.split("/")[-1].split(":")[0]
        skill_mounts.append(
            f"type=artifact,src={skill},dst=/var/oci-artifacts/skills/{name}"
        )
    agent_mounts: list[str] = []
    for agent in box.Agents:
        name = agent.split("/")[-1].split(":")[0]
        agent_mounts.append(
            f"type=artifact,src={agent},dst=/var/oci-artifacts/agents/{name}"
        )
    volumes: list[str] = []
    volumes.append(f"{box.MountedWorkspace}:{box.InternalWorkspace}")
    for mount in box.AdditionalMounts:
        volumes.append(f"{mount.From}:{mount.To}")

    cmd = [
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
        parent_pod_name,
    ]
    for volume in volumes:
        cmd.extend(["-v", volume])
    for skill_mount in skill_mounts:
        cmd.extend(["--mount", skill_mount])
    for agent_mount in agent_mounts:
        cmd.extend(["--mount", agent_mount])
    for key, value in box.Env.items():
        cmd.extend(["--env", f"{key}={value}"])
    if box.EnvFile is not None:
        cmd.extend(["--env-file", f"{box.EnvFile}"])
    cmd.extend([box.OCIImage, "/sbin/init"])

    return (box_container_name, cmd)


def assemble_run_mcp_cmds(
    mcp_server: list[MCPServerConfig], workspace_name: str, parent_pod_name: str
) -> tuple[dict[str, list[str]], ClaudeJSON]:
    mcp_servers_in_config: list[MCPServerConfig] = []
    create_mcp_container_cmds: dict[str, list[str]] = {}
    for mcp in mcp_server:
        mcp_name = mcp.OCIImage.rsplit("/", 1)[1].split(":")[0]
        container_name = f"{mcp_name}-{workspace_name}"
        cmd = [
            "podman",
            "run",
            "--name",
            container_name,
            "--replace",
            "--rm",
            "--pull",
            "never",
            "-d",
            "--security-opt",
            "label=disable",
            "--pod",
            parent_pod_name,
        ]
        for env_var in mcp.Env:
            for k, v in env_var.items():
                cmd.extend(["--env", f"{k}={v}"])
        cmd.append(mcp.OCIImage)

        create_mcp_container_cmds[container_name] = cmd

        mcp_servers_in_config.append(
            MCPServer(Name=mcp_name, Type="sse", URL=f"http://localhost:{mcp.Port}/sse")
        )

    return (create_mcp_container_cmds, ClaudeJSON(mcp_servers_in_config))


def run_aicrate(cfg: RunConfig):
    # pull images and artifacts prior to command assembly
    images: set[str] = set(
        [cfg.WorkBox.OCIImage, *[box.OCIImage for box in cfg.AgentBoxes]]
    )
    artifacts: set[str] = set(
        [
            *[skill for skill in cfg.WorkBox.Skills],
            *[agent for agent in cfg.WorkBox.Agents],
            *[skill for box in cfg.AgentBoxes for skill in box.Skills],
            *[agent for box in cfg.AgentBoxes for agent in box.Agents],
        ]
    )
    logger.info("Pulling images...")
    for image in images:
        engine.pull_image(image)
    logger.info("Pulling artifacts...")
    for artifact in artifacts:
        engine.pull_artifact(artifact)

    workspace_name = cfg.WorkBox.MountedWorkspace.name

    pod_name, create_pod_cmd = assemble_create_pod_cmd(workspace_name)
    workbox_container_name, create_container_cli_box = assemble_run_box_cmd(
        workspace_name, cfg.WorkBox, pod_name
    )

    create_agentbox_container_cmds: dict[str, list[str]] = {}
    i = 0
    for agentbox in cfg.AgentBoxes:
        name, cmd = assemble_run_box_cmd(
            f"{workspace_name}-agent-{i}", agentbox, pod_name
        )
        create_agentbox_container_cmds[name] = cmd
        i += 1

    # cmd to exec into aicrate workbox container
    exec_into_cli_box_cmd = [
        "podman",
        "exec",
        "-it",
        "--workdir",
        "/workspace",
        workbox_container_name,
        "/bin/bash",
    ]
    create_mcp_container_cmds, claude_json = assemble_run_mcp_cmds(
        cfg.MCPServer, workspace_name, pod_name
    )

    run_cmd_with_error_handler(create_pod_cmd, [], "Failed to create aicrate pod")
    run_cmd_with_error_handler(
        create_container_cli_box, [], "Failed to create aicrate container"
    )
    create_claude_json_cmd = [
        "podman",
        "exec",
        workbox_container_name,
        "sh",
        "-c",
        f"""cat > /root/.claude.json << \"EOF\"\n{claude_json.to_config()}\nEOF""",
    ]
    run_cmd_with_error_handler(
        create_claude_json_cmd, [], "Failed to create initial .claude.json"
    )
    for name, cmd in create_agentbox_container_cmds.items():
        run_cmd_with_error_handler(
            cmd, [], f"Failed to create AI agent container {name}"
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
            for name in create_agentbox_container_cmds.keys():
                # do not break on an exception and keep stopping AI agent containers
                try:
                    run_cmd_with_error_handler(
                        ["podman", "stop", name],
                        [],
                        f"Failed to stop AI agent container {name}",
                    )
                except Exception:
                    pass
            for name in create_mcp_container_cmds.keys():
                # do not break on an exception and keep stopping mcp containers
                try:
                    run_cmd_with_error_handler(
                        ["podman", "stop", name],
                        [],
                        f"Failed to stop MCP server container {name}",
                    )
                except Exception:
                    pass
