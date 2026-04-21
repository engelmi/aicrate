import argparse

from aicrate.common.command import run_cmd_with_error_handler


def push(args: argparse.Namespace):

    artifact = args.artifact[0]
    run_cmd_with_error_handler(
        ["podman", "artifact", "push", artifact], [], f"Failed to push '{artifact}'"
    )
