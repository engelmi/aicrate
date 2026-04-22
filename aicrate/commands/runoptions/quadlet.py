from abc import ABC
from dataclasses import dataclass
from pathlib import Path

from aicrate.commands.runoptions.config import RunConfig


class Serializable(ABC):

    def serialize(self) -> str: ...


@dataclass
class QuadletSectionUnit(Serializable):
    Description: str
    Before: list[str]
    After: list[str]

    def serialize(self):
        return f"""
[Unit]
Description={self.Description}
Before={' '.join(b for b in self.Before)}
After={' '.join(a for a in self.After)}"""


@dataclass
class QuadletSectionInstall(Serializable):
    WantedBy: list[str]

    def serialize(self):
        return f"""
[Install]
WantedBy={' '.join(w for w in self.WantedBy)}"""


@dataclass
class QuadletSectionPod(Serializable):
    PodName: str

    def serialize(self):
        return f"""
[Pod]
PodName={self.PodName}"""


@dataclass
class QuadletSectionContainer(Serializable):
    Image: str
    Pull: str
    Exec: str
    ContainerName: str
    Pod: str
    Mounts: list[str]
    Volumes: list[str]
    SecurityLabelDisable: bool
    EnvVariables: list[str]

    def serialize(self):
        mounts: list[str] = []
        for mount in self.Mounts:
            mounts.append(f"Mount={mount}")
        volumes: list[str] = []
        for volume in self.Volumes:
            volumes.append(f"Volume={volume}")
        env_vars: list[str] = []
        for var in self.EnvVariables:
            env_vars.append(f"Environment={var}")

        securitylabeldisable = f"{self.SecurityLabelDisable}".lower()

        return f"""
[Container]
Image={self.Image}
Pull={self.Pull}
Exec={self.Exec}
ContainerName={self.ContainerName}
Pod={self.Pod}
{'\n'.join(m for m in mounts)}
{'\n'.join(v for v in volumes)}
{'\n'.join(var for var in env_vars)}
SecurityLabelDisable={securitylabeldisable}"""


@dataclass
class QuadletPod(Serializable):
    Filepath: Path
    Unit: QuadletSectionUnit
    Pod: QuadletSectionPod
    Install: QuadletSectionInstall

    def serialize(self):
        return f"""
{self.Unit.serialize()}
{self.Pod.serialize()}
{self.Install.serialize()}
"""


@dataclass
class QuadletContainer(Serializable):
    Filepath: Path
    Unit: QuadletSectionUnit
    Container: QuadletSectionContainer
    Install: QuadletSectionInstall

    def serialize(self):
        return f"""
{self.Unit.serialize()}
{self.Container.serialize()}
{self.Install.serialize()}
"""


def build_from_config(
    cfg: RunConfig, output_dir: Path
) -> tuple[QuadletPod, list[QuadletContainer]]:
    workspace_name = cfg.WorkBox.MountedWorkspace.name

    pod_name = f"aicrate-{workspace_name}"
    pod = QuadletPod(
        Filepath=output_dir / Path(f"{pod_name}.pod"),
        Unit=QuadletSectionUnit(
            Description=f"Pod for {pod_name}",
            Before=[],
            After=["network.target"],
        ),
        Pod=QuadletSectionPod(
            PodName=pod_name,
        ),
        Install=QuadletSectionInstall(WantedBy=[]),
    )

    container_name = f"aicrate-{workspace_name}"

    skill_mounts: list[str] = []
    for skill in cfg.Skills:
        name = skill.split("/")[-1].split(":")[0]
        skill_mounts.append(
            f"type=artifact,src={skill},dst=/var/oci-artifacts/skills/{name}"
        )
    agent_mounts: list[str] = []
    for agent in cfg.Agents:
        name = agent.split("/")[-1].split(":")[0]
        agent_mounts.append(
            f"type=artifact,src={agent},dst=/var/oci-artifacts/agents/{name}"
        )

    volumes: list[str] = []
    volumes.append(
        f"{Path('~/.config/gcloud').expanduser().resolve()}:/root/.config/gcloud"
    )
    volumes.append(f"{cfg.WorkBox.MountedWorkspace}:{cfg.WorkBox.InternalWorkspace}")

    aicrate_container = QuadletContainer(
        Filepath=output_dir / Path(f"{container_name}.container"),
        Unit=QuadletSectionUnit(
            Description=f"aicrate container {workspace_name}",
            Before=[],
            After=[],
        ),
        Container=QuadletSectionContainer(
            Image=cfg.WorkBox.OCIImage,
            ContainerName=container_name,
            Pod=f"{pod_name}.pod",
            Exec="/sbin/init",
            Pull="never",
            SecurityLabelDisable=True,
            Mounts=[*skill_mounts, *agent_mounts],
            Volumes=volumes,
            EnvVariables=[],
        ),
        Install=QuadletSectionInstall(WantedBy=[]),
    )

    mcp_container: list[QuadletContainer] = []
    for mcp in cfg.MCPServer:
        mcp_name = mcp.OCIImage.rsplit("/", 1)[1].split(":")[0]
        env_vars: list[str] = mcp.get("env", [])

        mcp_container.append(
            QuadletContainer(
                Filepath=output_dir / Path(f"{mcp_name}.container"),
                Unit=QuadletSectionUnit(
                    Description=f"MCP server container for {mcp_name}",
                    Before=[],
                    After=[],
                ),
                Container=QuadletSectionContainer(
                    Image=mcp.OCIImage,
                    ContainerName=mcp_name,
                    Pod=f"{pod_name}.pod",
                    Exec="",
                    Pull="never",
                    SecurityLabelDisable=True,
                    Mounts=[],
                    Volumes=[],
                    EnvVariables=[
                        f"{k}={v}" for entry in env_vars for k, v in entry.items()
                    ],
                ),
                Install=QuadletSectionInstall(WantedBy=[]),
            )
        )

    return (pod, [aicrate_container, *mcp_container])
