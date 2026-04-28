import argparse

from aicrate.common.command import run_cmd_with_error_handler


def pull_artifact(args: argparse.Namespace):
    artifact = args.artifact[0]
    do_pull_artifact(artifact)


def do_pull_artifact(artifact: str):
    run_cmd_with_error_handler(
        ["podman", "artifact", "pull", artifact],
        [],
        f"Failed to pull artifact '{artifact}'",
    )


def pull_image(args: argparse.Namespace):
    image = args.image[0]
    do_pull_image(image)


def do_pull_image(image: str):
    run_cmd_with_error_handler(
        ["podman", "pull", image], [], f"Failed to pull image '{image}'"
    )
