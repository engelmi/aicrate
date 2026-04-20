import argparse
import json
from dataclasses import dataclass

from aicrate.commands.consts import ArtifactTypeAgentManifest, ArtifactTypeSkillManifest
from aicrate.common.command import run_cmd, run_cmd_with_error_handler


@dataclass
class ListedArtifact:
    Name: str
    Digest: str
    ArtifactType: str


def list(args: argparse.Namespace):
    artifacts: dict[str, ListedArtifact] = {
        ArtifactTypeAgentManifest: [],
        ArtifactTypeSkillManifest: [],
    }

    res = run_cmd_with_error_handler(
        ["podman", "artifact", "ls", "--format", "{{.Repository}}:{{.Tag}}"],
        [],
        "Failed to list artifacts",
    )
    for artifact in res.split("\n"):
        if not artifact:
            continue
        output = run_cmd(["podman", "artifact", "inspect", artifact], [], True)
        if output:
            json_output = json.loads(output)
            artifactType = json_output.get("Manifest", {}).get("artifactType", None)
            if artifactType in artifacts.keys():
                artifacts[artifactType].append(
                    ListedArtifact(
                        Name=json_output.get("Name", ""),
                        Digest=json_output.get("Digest", ""),
                        ArtifactType=artifactType,
                    )
                )

    print_listed_artifacts(artifacts)


def print_listed_artifacts(artifacts: dict[str, ListedArtifact]):
    skills = artifacts.get(ArtifactTypeSkillManifest, [])
    if skills:
        print("Skills")
    for skill in artifacts.get(ArtifactTypeSkillManifest, []):
        print(f"\t{skill.Name}")

    agents = artifacts.get(ArtifactTypeAgentManifest, [])
    if agents:
        print("Agents")
    for agent in artifacts.get(ArtifactTypeAgentManifest, []):
        print(f"\t{agent.Name}")
