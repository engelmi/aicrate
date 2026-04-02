import pty
from pathlib import Path

from claudebox.common.command import run_cmd_with_error_handler

def run_claudebox(config: dict, workspace_dir: Path):
    claudebox_config = config.get("claudebox", {})
    skills_config = config.get("skills", {})
    agents_config = config.get("agents", {})
    mcp_config = config.get("mcp", {})

    pod_name=f"claudebox-{workspace_dir.name}"
    create_pod_cmd = [
        "podman", "pod", "create", "--replace", "--exit-policy", "stop", "--infra-name", f"{pod_name}-infra", "--name", pod_name, 
    ]

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

    create_container_claude_box_cmd = [
        "podman", "run", "--name", container_name, "--replace", "--rm", "--pull", "never", "-d", "--security-opt", "label=disable", "--pod", pod_name
    ]
    for volume in volumes:
        create_container_claude_box_cmd.extend(["-v", volume])
    for skill_mount in skill_mounts:
        create_container_claude_box_cmd.extend(["--mount", skill_mount])
    for agent_mount in agent_mounts:
        create_container_claude_box_cmd.extend(["--mount", agent_mount])
    create_container_claude_box_cmd.extend([claudebox_config.get("image", ""), "/sbin/init"])

    exec_into_claude_box_cmd = [
        "podman", "exec", "-it", container_name, "/bin/bash"
    ]

    run_cmd_with_error_handler(create_pod_cmd, [], "Failed to create claudebox pod")
    run_cmd_with_error_handler(create_container_claude_box_cmd, [], "Failed to create claudebox container")
    try:
        pty.spawn(exec_into_claude_box_cmd)
    finally:
        run_cmd_with_error_handler(["podman", "stop", pod_name], [], f"Failed to stop {pod_name}")
