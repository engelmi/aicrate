import argparse

from aicrate.common.command import run_cmd_with_error_handler


def push_artifact(args: argparse.Namespace):

    artifact = args.artifact[0]
    run_cmd_with_error_handler(
        ["podman", "artifact", "push", artifact], [], f"Failed to push '{artifact}'"
    )


def push_image(args: argparse.Namespace):

    image = args.image[0]
    run_cmd_with_error_handler(
        ["podman", "image", "push", image], [], f"Failed to push '{image}'"
    )
