from pathlib import Path

from aicrate.commands.consts import (
    ArtifactAnnotationGitRemote,
    ArtifactAnnotationGitVersion,
)
from aicrate.common.command import run_cmd, run_cmd_with_error_handler


def pull_artifact(artifact: str) -> str:
    return run_cmd_with_error_handler(
        ["podman", "artifact", "pull", artifact],
        [],
        f"Failed to pull artifact '{artifact}'",
    )


def pull_image(image: str) -> str:
    return run_cmd_with_error_handler(
        ["podman", "pull", image], [], f"Failed to pull image '{image}'"
    )


def push_artifact(artifact: str) -> str:
    return run_cmd_with_error_handler(
        ["podman", "artifact", "push", artifact], [], f"Failed to push '{artifact}'"
    )


def push_image(image: str) -> str:
    return run_cmd_with_error_handler(
        ["podman", "image", "push", image], [], f"Failed to push '{image}'"
    )


def list_artifacts() -> str:
    return run_cmd_with_error_handler(
        ["podman", "artifact", "ls", "--format", "{{.Repository}}:{{.Tag}}"],
        [],
        "Failed to list artifacts",
    )


def inspect_artifact(artifact: str, supress_error: bool = False) -> str:
    return run_cmd(["podman", "artifact", "inspect", artifact], [], supress_error)


def bulid_image(image: str, dir: str) -> str:
    return run_cmd_with_error_handler(
        [
            "podman",
            "build",
            "-f",
            "Containerfile",
            "-t",
            image,
            f"{dir}",
        ],
        [],
        f"Failed to build workbox from Containerfile in '{dir}'",
    )


def build_artifact(
    tag: str, resource: Path, artifact_type: str, git_remote: str, git_version: str
) -> str:
    return run_cmd_with_error_handler(
        [
            "podman",
            "artifact",
            "add",
            "--replace",
            tag,
            resource,
            "--type",
            artifact_type,
            "--annotation",
            f"{ArtifactAnnotationGitRemote}={git_remote}",
            "--annotation",
            f"{ArtifactAnnotationGitVersion}={git_version}",
        ],
        [],
        f"Failed to build OCI artifact from tarball '{resource}'",
    )
