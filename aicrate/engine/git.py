from pathlib import Path

from aicrate.common.command import run_cmd


def current_commit_hash(root_dir: Path) -> str:
    return run_cmd(["git", "-C", root_dir, "rev-parse", "HEAD"], [])


def current_remote_url(root_dir: Path) -> str:
    return run_cmd(["git", "-C", root_dir, "config", "--get", "remote.origin.url"], [])
