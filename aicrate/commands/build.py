import argparse
import shutil
from pathlib import Path
from typing import Optional

import aicrate.engine.git as git
import aicrate.engine.podman as engine
import aicrate.engine.tar as tar
from aicrate.commands.consts import (
    ArtifactTypeAgentManifest,
    ArtifactTypeSkillManifest,
)
from aicrate.logger import logger

TMP_BUILD_DIR = Path("/var/tmp/aicrate")


def prune(args: argparse.Namespace):
    if TMP_BUILD_DIR.exists():
        shutil.rmtree(TMP_BUILD_DIR)


def build_workbox(args: argparse.Namespace):

    tag_registry = "quay.io"
    tag_organization = "aicrate"
    name = "claudebox"
    tag_version = "latest"

    tag = f"{tag_registry}/{tag_organization}/{name}:{tag_version}"
    dir = Path(args.dir).expanduser().resolve()
    engine.bulid_image(tag, dir)


def build_agent(args: argparse.Namespace):
    build_artifact(
        dir=Path(args.dir),
        subgroup=args.subgroup,
        tag_registry=args.tag_registry,
        tag_organization=args.tag_organization,
        tag_version=args.tag_version,
        artifact_type=ArtifactTypeAgentManifest,
    )


def build_skill(args: argparse.Namespace):
    build_artifact(
        dir=Path(args.dir),
        subgroup=args.subgroup,
        tag_registry=args.tag_registry,
        tag_organization=args.tag_organization,
        tag_version=args.tag_version,
        artifact_type=ArtifactTypeSkillManifest,
    )


def build_artifact(
    dir: Path,
    subgroup: Optional[str],
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
    if subgroup:
        artifact_tag = f"{tag_registry}/{tag_organization}/{subgroup}/{artifact_dir.stem}:{tag_version}"

    tar.create_tarball(tmp_tarball, artifact_dir)

    git_remote = "N/A"
    git_version = "N/A"
    try:
        version = git.current_commit_hash(artifact_dir.parent)
        if version:
            git_version = version.strip()
        remote = git.current_remote_url(artifact_dir.parent)
        if remote:
            git_remote = remote.strip()

    except Exception as ex:
        logger.warning("Failed to get git information, proceeding.")
        logger.debug(f"Failure reason: {ex}")

    engine.build_artifact(
        artifact_tag, tmp_tarball, artifact_type, git_remote, git_version
    )
