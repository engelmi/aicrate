import argparse
import os
from pathlib import Path
from typing import Sequence, Tuple

from aicrate.commands import build, list, pull, push, run
from aicrate.logger import LogLevel
from aicrate.version import version


def parse_log_level_option(option: str) -> LogLevel:
    return LogLevel.from_string(option)


def parse_arguments(
    args: Sequence[str] = None,
) -> Tuple[argparse.Namespace, argparse.ArgumentParser]:
    parser = argparse.ArgumentParser(
        description="aicrate - containerize your AI agent",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("--version", action="version", version=version())
    parser.add_argument(
        "--log-level",
        dest="log_level",
        default=LogLevel.INFO,
        type=parse_log_level_option,
        help="Set log level used by the application",
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        type=Path,
        help="Path to the log file. If not given, logs will be printed to stderr.",
    )

    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.required = False

    add_run_parser(subparsers)
    add_build_parser(subparsers)
    add_push_parser(subparsers)
    add_list_parser(subparsers)

    return parser.parse_args(args), parser


def add_run_parser(parent_parser: argparse._SubParsersAction):
    run_parser = parent_parser.add_parser("run", help="Run a new aicrate")
    run_parser.set_defaults(func=run.run)

    run_parser.add_argument(
        "--config",
        "-c",
        help=("Configuration of aicrate to use."),
        dest="config",
        type=str,
    )
    run_parser.add_argument(
        "--mode",
        "-m",
        help=("The mode how to run aicrate"),
        dest="mode",
        choices=["systemd", "podman"],
        default="podman",
    )

    run_parser.add_argument(
        "--workspace",
        "-w",
        help=(
            "The directory on the host which gets mounted into aicrate as workspace."
        ),
        dest="workspace",
        type=str,
        default=os.getcwd(),
    )
    run_parser.add_argument(
        "--output-dir",
        "-o",
        help=("The directory to write the generated quadlet files to"),
        dest="output_dir",
        type=str,
        default="~/.config/containers/systemd",
    )

    run_parser.add_argument(
        "--detach",
        "-d",
        dest="detached",
        help=("Run aicrate in detached mode."),
        action="store_true",
    )


def add_build_parser(parent_parser: argparse._SubParsersAction):
    build_parser = parent_parser.add_parser(
        "build", help="Build an OCI artifact for skills or agents"
    )
    build_parser.set_defaults(func=lambda _: build_parser.print_help())

    subparsers = build_parser.add_subparsers(dest="build_subcommand")
    add_build_skill_parser(subparsers)
    add_build_agent_parser(subparsers)
    add_build_workbox_parser(subparsers)
    add_build_prune_parser(subparsers)


def _add_artifact_parser_arguments(parser):
    parser.add_argument(
        "--dir",
        help=("Directory containing the artifact."),
        dest="dir",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--oci-subgroup",
        help=("Subgroup part of the OCI artifact name"),
        dest="subgroup",
        type=str,
        default="",
    )

    parser.add_argument(
        "--oci-tag-registry",
        help=("Registry part of the tag for the OCI artifact"),
        dest="tag_registry",
        type=str,
        default="quay.io",
    )
    parser.add_argument(
        "--oci-tag-organization",
        help=("Organization part of the tag for the OCI artifact"),
        dest="tag_organization",
        type=str,
        default="aicrate",
    )
    parser.add_argument(
        "--oci-tag-version",
        help=("Version part of the tag for the OCI artifact"),
        dest="tag_version",
        type=str,
        default="latest",
    )


def add_build_skill_parser(parent_parser: argparse._SubParsersAction):
    build_skill_parser = parent_parser.add_parser(
        "skill", help="Build an OCI artifact from a skill"
    )
    build_skill_parser.set_defaults(func=build.build_skill)
    _add_artifact_parser_arguments(build_skill_parser)


def add_build_agent_parser(parent_parser: argparse._SubParsersAction):
    build_agent_parser = parent_parser.add_parser(
        "agent", help="Build an OCI artifact from an agent"
    )
    build_agent_parser.set_defaults(func=build.build_agent)
    _add_artifact_parser_arguments(build_agent_parser)


def add_build_workbox_parser(parent_parser: argparse._SubParsersAction):
    build_workbox_parser = parent_parser.add_parser(
        "workbox", help="Build the workbox of aicrate"
    )
    build_workbox_parser.set_defaults(func=build.build_workbox)
    build_workbox_parser.add_argument(
        "--dir",
        help=("Directory containing the Containerfile."),
        dest="dir",
        type=str,
        required=True,
    )


def add_build_prune_parser(parent_parser: argparse._SubParsersAction):
    build_agent_parser = parent_parser.add_parser(
        "prune", help="Prune all temporary build artifacts"
    )
    build_agent_parser.set_defaults(func=build.prune)


def add_list_parser(parent_parser: argparse._SubParsersAction):
    list_parser = parent_parser.add_parser(
        "list", aliases=["ls"], help="List OCI artifacts"
    )
    list_parser.set_defaults(func=list.print_listed_artifacts)

    list_parser.add_argument(
        "--agents",
        help=("Show only agents"),
        action="store_true",
    )
    list_parser.add_argument(
        "--skills",
        help=("Show only skills"),
        action="store_true",
    )
    list_parser.add_argument(
        "--json",
        help=("Output as json"),
        action="store_true",
    )


def add_push_parser(parent_parser: argparse._SubParsersAction):
    push_parser = parent_parser.add_parser(
        "push", help="Push OCI artifacts or images to registry"
    )

    subparsers = push_parser.add_subparsers(dest="push_subcommand")

    push_artifact_parser = subparsers.add_parser(
        "artifact", help="Push an OCI artifact to registry"
    )
    push_artifact_parser.set_defaults(func=push.push_artifact)
    push_artifact_parser.add_argument(
        "artifact",
        help=("Artifact to push to registry"),
        nargs=1,
    )

    push_image_parser = subparsers.add_parser(
        "image", help="Push an OCI image to registry"
    )
    push_image_parser.set_defaults(func=push.push_image)
    push_image_parser.add_argument(
        "image",
        help=("Image to push to registry"),
        nargs=1,
    )


def add_pull_parser(parent_parser: argparse._SubParsersAction):
    pull_parser = parent_parser.add_parser(
        "pull", help="Pull OCI artifacts from registry", usage="aicrate pull <artifact>"
    )
    pull_parser.set_defaults(func=pull.pull)

    pull_parser.add_argument(
        "artifact",
        help=("Artifact to pull from registry"),
        nargs=1,
    )
