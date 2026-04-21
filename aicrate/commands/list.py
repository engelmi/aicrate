import argparse
import json
from dataclasses import asdict, dataclass

import tabulate

from aicrate.commands.consts import (
    ArtifactAnnotationGitRemote,
    ArtifactAnnotationGitVersion,
    ArtifactTypeAgentManifest,
    ArtifactTypeSkillManifest,
)
from aicrate.common.command import run_cmd, run_cmd_with_error_handler


@dataclass
class ListedArtifact:
    Name: str
    Digest: str
    ArtifactType: str
    GitRemote: str
    GitVersion: str


def list_artifacts() -> list[ListedArtifact]:
    artifacts: list[ListedArtifact] = []

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
            if artifactType in [ArtifactTypeSkillManifest, ArtifactTypeAgentManifest]:
                artifacts.append(
                    ListedArtifact(
                        Name=json_output.get("Name", ""),
                        Digest=json_output.get("Digest", ""),
                        ArtifactType=artifactType,
                        GitRemote=json_output.get("Manifest", {})
                        .get("annotations", {})
                        .get(ArtifactAnnotationGitRemote),
                        GitVersion=json_output.get("Manifest", {})
                        .get("annotations", {})
                        .get(ArtifactAnnotationGitVersion),
                    )
                )

    return artifacts


def print_listed_artifacts(args: argparse.Namespace):

    artifacts: list[ListedArtifact] = list_artifacts()

    show_skills = args.skills
    show_agents = args.agents

    if args.json:
        data = {"artifacts": []}
        skills = [
            asdict(a) for a in artifacts if a.ArtifactType == ArtifactTypeSkillManifest
        ]
        agents = [
            asdict(a) for a in artifacts if a.ArtifactType == ArtifactTypeAgentManifest
        ]
        if show_skills:
            data["artifacts"].extend(skills)
        if show_agents:
            data["artifacts"].extend(agents)

        print(json.dumps(data, indent=2))
        return

    table_data = []
    for artifact in artifacts:
        atype = "Unknown"
        if artifact.ArtifactType == ArtifactTypeSkillManifest:
            if not show_skills and show_agents:
                continue
            atype = "Skill"

        elif artifact.ArtifactType == ArtifactTypeAgentManifest:
            if show_skills and not show_agents:
                continue
            atype = "Agent"

        table_data.append(
            [atype, artifact.Name, artifact.GitRemote, artifact.GitVersion]
        )

    print(
        tabulate.tabulate(
            tabular_data=table_data,
            headers=["Type", "Name", "Remote", "Version"],
            tablefmt="simple_outline",
        )
    )
