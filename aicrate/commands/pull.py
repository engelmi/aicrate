import argparse

from aicrate.common.command import run_cmd_with_error_handler


def pull(args: argparse.Namespace):

    artifact = args.artifact[0]
    run_cmd_with_error_handler(
        ["podman", "artifact", "pull", artifact], [], f"Failed to pull '{artifact}'"
    )
