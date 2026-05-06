import os
import json
import argparse
import datetime
from urllib.parse import urlsplit
from typing import Tuple, Sequence, Optional
from pathlib import Path

from github import Github
from gitlab import Gitlab

import common


def wiki_setup(func):
    def wrapper(*args, **kwargs):
        output_dir = args[0]
        common.ensure_directories(output_dir)

        return func(*args, **kwargs)

    return wrapper


def update_last_fetched(func):
    def wrapper(*args, **kwargs):
        output_dir = args[0]

        # read last fetched timestamp
        last_updated_file = output_dir / "last_updated"
        last_updated_timestamp: Optional[datetime.datetime] = (
            None if "since" not in kwargs else kwargs["since"]
        )
        if last_updated_file.exists():
            with open(last_updated_file, "r") as f:
                last_updated_timestamp = datetime.datetime.strptime(
                    f.read(), "%Y-%m-%d %H:%M:%S"
                )

        # set the since parameter based on last time fetched timestamp
        # and run actual function
        kwargs["since"] = last_updated_timestamp
        result = func(*args, **kwargs)

        # update last fetched timestamp
        last_updated_timestamp = datetime.datetime.now(datetime.UTC)
        with open(last_updated_file, "w") as f:
            f.write(last_updated_timestamp.strftime("%Y-%m-%d %H:%M:%S"))

        return result

    return wrapper


@wiki_setup
@update_last_fetched
def fetch_github_issues(
    output_dir: Path,
    repository: str,
    token: Optional[str],
    since: Optional[datetime.datetime] = None,
):
    g = Github(token)
    repo = g.get_repo(repository)

    issues = []
    if since is None:
        issues = repo.get_issues(state="all")
    else:
        issues = repo.get_issues(state="all", since=since)

    # Note: GitHub uses the term "issue" for both - PR and actual issues
    for issue in issues:
        out_dir = (
            common.get_pulls_dir(output_dir)
            if issue.pull_request
            else common.get_issues_dir(output_dir)
        )
        out_dir = (
            out_dir / common.WIKI_OPEN_DIR_NAME
            if issue.state == "open"
            else out_dir / common.WIKI_CLOSED_DIR_NAME
        )
        out_path = out_dir / f"{issue.number}"

        with open(out_path, "w") as f:
            f.write(json.dumps(issue.raw_data, indent=2, sort_keys=True))


@wiki_setup
@update_last_fetched
def fetch_gitlab_issues(
    output_dir: Path,
    repository: str,
    base_url: str,
    token: Optional[str],
    since: Optional[datetime.datetime] = None,
):
    gl = Gitlab(
        url=base_url,
        private_token=token,
    )

    project = gl.projects.get(repository)
    issues = project.issues.list(created_after=since, get_all=True)

    out_base_dir = common.get_issues_dir(output_dir)
    for issue in issues:
        out_dir = (
            out_base_dir / common.WIKI_OPEN_DIR_NAME
            if issue.state == "opened"
            else out_base_dir / common.WIKI_CLOSED_DIR_NAME
        )
        out_path = out_dir / f"{issue.iid}"
        with open(out_path, "w") as f:
            f.write(json.dumps(issue.attributes, indent=2, sort_keys=True))

    out_base_dir = common.get_pulls_dir(output_dir)
    mrs = project.mergerequests.list(updated_after=since, get_all=True)
    for mr in mrs:
        out_dir = (
            out_base_dir / common.WIKI_OPEN_DIR_NAME
            if mr.state == "opened"
            else out_base_dir / common.WIKI_CLOSED_DIR_NAME
        )
        out_path = out_dir / f"{mr.iid}"
        with open(out_path, "w") as f:
            f.write(json.dumps(mr.attributes, indent=2, sort_keys=True))


def parse_arguments(
    args: Sequence[str] = None,
) -> Tuple[argparse.Namespace, argparse.ArgumentParser]:
    parser = argparse.ArgumentParser(
        description="build-kb - Fetch data for a local knowledge base of open source issues",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--root-dir",
        dest="root_dir",
        required=True,
        type=common.parse_path,
        help="Set root directory of knowledge base",
    )
    parser.add_argument(
        "--project-url",
        dest="project_url",
        required=True,
        type=str,
        help="The URL of the project",
    )
    parser.add_argument(
        "--token",
        dest="token",
        type=str,
        default=os.getenv("API_TOKEN", None),
        help="The API token used to access the platform API",
    )

    return parser.parse_args(args), parser


if __name__ == "__main__":
    cli_args, parser = parse_arguments()

    url_parts = urlsplit(cli_args.project_url)
    host = f"{url_parts.scheme}://{url_parts.netloc}"
    repo = f"{url_parts.path}".removeprefix("/")
    pathified_repo = repo.replace("/", "_")

    if common.Platform.GitHub.value in url_parts.netloc:
        wiki_dir = Path(cli_args.root_dir, common.Platform.GitHub.value, pathified_repo)
        wiki_dir.mkdir(parents=True, exist_ok=True)

        fetch_github_issues(wiki_dir, repository=repo, token=cli_args.token)
    elif common.Platform.Gitlab.value in url_parts.netloc:
        wiki_dir = Path(cli_args.root_dir, common.Platform.Gitlab.value, pathified_repo)
        wiki_dir.mkdir(parents=True, exist_ok=True)

        fetch_gitlab_issues(
            wiki_dir, repository=repo, base_url=host, token=cli_args.token
        )
