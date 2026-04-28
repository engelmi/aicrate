from pathlib import Path

from aicrate.common.command import run_cmd_with_error_handler


def create_tarball(output_name: str, dir: Path) -> str:
    return run_cmd_with_error_handler(
        [
            "tar",
            "-c",
            "-f",
            output_name,
            "-C",
            f"{dir.parent}",
            f"{dir.name}",
        ],
        [],
        f"Failed to build temporary tarball for artifact '{dir}'",
    )
