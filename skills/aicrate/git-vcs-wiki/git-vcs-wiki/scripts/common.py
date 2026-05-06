import os
import argparse
from typing import Tuple, Sequence
from pathlib import Path
from enum import StrEnum

WIKI_DIR_NAME = "git-vcs-wiki"
WIKI_ISSUE_DIR_NAME = "issues"
WIKI_PULL_DIR_NAME = "pulls"
WIKI_OPEN_DIR_NAME = "open"
WIKI_CLOSED_DIR_NAME = "closed"


class Platform(StrEnum):
    GitHub = "github"
    Gitlab = "gitlab"


def get_pulls_dir(base_dir: Path) -> Path:
    return base_dir / WIKI_PULL_DIR_NAME


def get_issues_dir(base_dir: Path) -> Path:
    return base_dir / WIKI_ISSUE_DIR_NAME


def ensure_directories(base_dir: Path):
    pulls_dir = get_pulls_dir(base_dir)
    issues_dir = get_issues_dir(base_dir)

    open_issues_dir = issues_dir / WIKI_OPEN_DIR_NAME
    open_issues_dir.mkdir(parents=True, exist_ok=True)
    open_pulls_dir = pulls_dir / WIKI_OPEN_DIR_NAME
    open_pulls_dir.mkdir(parents=True, exist_ok=True)

    closed_issues_dir = issues_dir / WIKI_CLOSED_DIR_NAME
    closed_issues_dir.mkdir(parents=True, exist_ok=True)
    closed_pulls_dir = pulls_dir / WIKI_CLOSED_DIR_NAME
    closed_pulls_dir.mkdir(parents=True, exist_ok=True)


def default_root_dir(args: argparse.Namespace) -> Path:
    print(Path(os.getcwd()))


def parse_path(option: str) -> Path:
    return Path(option).expanduser().resolve()


def parse_arguments(
    args: Sequence[str] = None,
) -> Tuple[argparse.Namespace, argparse.ArgumentParser]:
    parser = argparse.ArgumentParser(
        description="common - Fetch data for a local knowledge base of open source issues",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_add = subparsers.add_parser(
        "root-dir", help="Prints the default root directory"
    )
    parser_add.set_defaults(func=default_root_dir)

    return parser.parse_args(args), parser


if __name__ == "__main__":
    cli_args, parser = parse_arguments()
    cli_args.func(cli_args)
