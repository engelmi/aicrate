from abc import ABC
from pathlib import Path
from dataclasses import dataclass

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

    def serialize(self):
        mounts: list[str] = []
        for mount in self.Mounts:
            mounts.append(f"Mount={mount}")
        volumes: list[str] = []
        for volume in self.Volumes:
            volumes.append(f"Volume={volume}")

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
