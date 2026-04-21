import argparse
import shutil
from pathlib import Path

from aicrate.commands.consts import (
    ArtifactAnnotationGitRemote,
    ArtifactAnnotationGitVersion,
    ArtifactTypeAgentManifest,
    ArtifactTypeSkillManifest,
)
from aicrate.common.command import run_cmd, run_cmd_with_error_handler
from aicrate.logger import logger

TMP_BUILD_DIR = Path("/var/tmp/aicrate")


def prune(args: argparse.Namespace):
    if TMP_BUILD_DIR.exists():
        shutil.rmtree(TMP_BUILD_DIR)


def build_agent(args: argparse.Namespace):
    build_artifact(
        dir=Path(args.dir),
        tag_registry=args.tag_registry,
        tag_organization=args.tag_organization,
        tag_version=args.tag_version,
        artifact_type=ArtifactTypeAgentManifest,
    )


def build_skill(args: argparse.Namespace):
    build_artifact(
        dir=Path(args.dir),
        tag_registry=args.tag_registry,
        tag_organization=args.tag_organization,
        tag_version=args.tag_version,
        artifact_type=ArtifactTypeSkillManifest,
    )


def build_artifact(
    dir: Path,
    tag_registry: str,
    tag_organization: str,
    tag_version: str,
    artifact_type: str,
):
    # Create temporary directory to store temporary tarballs in
    TMP_BUILD_DIR.mkdir(mode=0o766, parents=True, exist_ok=True)

    artifact_dir = dir.expanduser().resolve()
    tmp_tarball = TMP_BUILD_DIR / f"{artifact_dir.stem}.tar"

    artifact_tag = (
        f"{tag_registry}/{tag_organization}/{artifact_dir.stem}:{tag_version}"
    )

    run_cmd_with_error_handler(
        [
            "tar",
            "-c",
            "-f",
            tmp_tarball,
            "-C",
            f"{artifact_dir.parent}",
            f"{artifact_dir.name}",
        ],
        [],
        f"Failed to build temporary tarball for artifact '{artifact_dir}'",
    )

    git_remote = "N/A"
    git_version = "N/A"
    try:
        version = run_cmd(["git", "-C", artifact_dir.parent, "rev-parse", "HEAD"], [])
        if version:
            git_version = version.strip()
        remote = run_cmd(
            ["git", "-C", artifact_dir.parent, "config", "--get", "remote.origin.url"],
            [],
        )
        if remote:
            git_remote = remote.strip()

    except Exception as ex:
        logger.warning("Failed to get git information, proceeding.")
        logger.debug(f"Failure reason: {ex}")

    run_cmd_with_error_handler(
        [
            "podman",
            "artifact",
            "add",
            "--replace",
            artifact_tag,
            tmp_tarball,
            "--type",
            artifact_type,
            "--annotation",
            f"{ArtifactAnnotationGitRemote}={git_remote}",
            "--annotation",
            f"{ArtifactAnnotationGitVersion}={git_version}",
        ],
        [],
        f"Failed to build OCI artifact from tarball '{tmp_tarball}'",
    )
