import pty
from pathlib import Path

from aicrate.common.command import run_cmd_with_error_handler
from aicrate.model import ClaudeJSON, MCPServer


def run_aicrate(config: dict, workspace_dir: Path):
    aicrate_config = config.get("aicrate", {})
    skills_config = config.get("skills", {})
    agents_config = config.get("agents", {})
    mcp_config = config.get("mcp", {})

    pod_name = f"aicrate-{workspace_dir.name}"
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

    box_container_name = f"aicrate-{workspace_dir.name}"
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
    volumes.append(
        f"{Path('~/.config/gcloud').expanduser().resolve()}:/root/.config/gcloud"
    )
    volumes.append(f"{workspace_dir}:/workspace")

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
    create_container_cli_box.extend([aicrate_config.get("image", ""), "/sbin/init"])

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
    for mcp in mcp_config:
        image: str = mcp.get("image", "")
        mcp_name = image.rsplit("/", 1)[1].split(":")[0]
        env_vars: list[str] = mcp.get("env", [])
        cmd = [
            "podman",
            "run",
            "--name",
            f"{mcp_name}-{workspace_dir.name}",
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
        for env_var in env_vars:
            for k, v in env_var.items():
                cmd.extend(["--env", f"{k}={v}"])
        cmd.append(image)

        create_mcp_container_cmds[mcp_name] = cmd

        port = mcp.get("port", "")
        mcp_servers_in_config.append(
            MCPServer(Name=mcp_name, Type="sse", URL=f"http://localhost:{port}/sse")
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
        run_cmd_with_error_handler(
            ["podman", "stop", pod_name], [], f"Failed to stop {pod_name}"
        )
        for name in create_mcp_container_cmds.keys():
            # do not break on an exception and keep stopping mcp containers
            try:
                run_cmd_with_error_handler(
                    ["podman", "stop", f"{name}-{workspace_dir.name}"],
                    [],
                    f"Failed to stop MCP server {name}",
                )
            except Exception:
                pass
