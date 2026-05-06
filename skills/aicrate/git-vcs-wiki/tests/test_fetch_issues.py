import json
import pytest
import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

# ensure the PYTHONPATH is set to the scripts directory
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "git-vcs-wiki" / "scripts"))

import fetch_issues


class TestWikiSetupDecorator:

    def test_wiki_setup_calls_ensure_directories(self, tmp_path):

        @fetch_issues.wiki_setup
        def dummy_function(output_dir):
            return "success"

        with patch("common.ensure_directories") as mock_ensure:
            result = dummy_function(tmp_path)

            mock_ensure.assert_called_once_with(tmp_path)
            assert result == "success"

    def test_wiki_setup_passes_args_through(self, tmp_path):

        @fetch_issues.wiki_setup
        def dummy_function(output_dir, arg1, arg2, kwarg1=None):
            return (output_dir, arg1, arg2, kwarg1)

        with patch("common.ensure_directories"):
            result = dummy_function(tmp_path, "a", "b", kwarg1="c")

            assert result == (tmp_path, "a", "b", "c")


class TestUpdateLastFetchedDecorator:

    def test_update_last_fetched_no_existing_file(self, tmp_path):

        @fetch_issues.update_last_fetched
        def dummy_function(output_dir, since=None):
            return since

        result = dummy_function(tmp_path)

        # Should be called with since=None
        assert result is None

        # Should create last_updated file
        last_updated_file = tmp_path / "last_updated"
        assert last_updated_file.exists()

        # Verify timestamp format
        with open(last_updated_file) as f:
            timestamp_str = f.read()
            datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

    def test_update_last_fetched_with_existing_file(self, tmp_path):

        @fetch_issues.update_last_fetched
        def dummy_function(output_dir, since=None):
            return since

        # Create existing last_updated file
        last_updated_file = tmp_path / "last_updated"
        existing_timestamp = datetime.datetime(2024, 1, 1, 12, 0, 0)
        with open(last_updated_file, "w") as f:
            f.write(existing_timestamp.strftime("%Y-%m-%d %H:%M:%S"))

        result = dummy_function(tmp_path)

        # Should be called with the existing timestamp
        assert result == existing_timestamp

        # Should update the file with new timestamp
        with open(last_updated_file) as f:
            new_timestamp_str = f.read()
            new_timestamp = datetime.datetime.strptime(
                new_timestamp_str, "%Y-%m-%d %H:%M:%S"
            )
            # New timestamp should be after the old one
            assert new_timestamp > existing_timestamp

    def test_update_last_fetched_preserves_other_kwargs(self, tmp_path):

        @fetch_issues.update_last_fetched
        def dummy_function(output_dir, since=None, other_param=None):
            return (since, other_param)

        result = dummy_function(tmp_path, other_param="test_value")

        assert result[1] == "test_value"


class TestFetchGithubIssues:

    @patch("fetch_issues.Github")
    @patch("common.ensure_directories")
    def test_fetch_github_issues_no_since(
        self, mock_ensure_dirs, mock_github_class, tmp_path
    ):

        # Setup mock GitHub API
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        # Create mock issues
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.state = "open"
        mock_issue.pull_request = None
        mock_issue.raw_data = {"id": 123, "title": "Test issue"}

        mock_repo.get_issues.return_value = [mock_issue]

        # Create directory structure
        issues_dir = tmp_path / "issues" / "open"
        issues_dir.mkdir(parents=True, exist_ok=True)

        # Call function (note: decorators will be applied)
        fetch_issues.fetch_github_issues(
            tmp_path, "test/repo", "fake_token", since=None
        )

        # Verify GitHub API calls
        mock_github_class.assert_called_once_with("fake_token")
        mock_github.get_repo.assert_called_once_with("test/repo")
        mock_repo.get_issues.assert_called_once_with(state="all")

        # Verify file was written
        issue_file = issues_dir / "123"
        assert issue_file.exists()

        with open(issue_file) as f:
            data = json.load(f)
            assert data == {"id": 123, "title": "Test issue"}

    @patch("fetch_issues.Github")
    @patch("common.ensure_directories")
    def test_fetch_github_issues_with_since(
        self, mock_ensure_dirs, mock_github_class, tmp_path
    ):
        """Test fetching GitHub issues with since parameter"""

        # Setup mock GitHub API
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo
        mock_repo.get_issues.return_value = []

        since_timestamp = datetime.datetime(2024, 1, 1, 12, 0, 0)

        # Call function
        fetch_issues.fetch_github_issues(
            tmp_path, "test/repo", "fake_token", since=since_timestamp
        )

        # Verify since parameter was passed
        mock_repo.get_issues.assert_called_once_with(state="all", since=since_timestamp)

    @patch("fetch_issues.Github")
    @patch("common.ensure_directories")
    def test_fetch_github_issues_pull_request(
        self, mock_ensure_dirs, mock_github_class, tmp_path
    ):
        """Test that pull requests are saved to pulls directory"""

        # Setup mock GitHub API
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        # Create mock PR
        mock_pr = MagicMock()
        mock_pr.number = 456
        mock_pr.state = "closed"
        mock_pr.pull_request = {
            "url": "https://api.github.com/repos/test/repo/pulls/456"
        }
        mock_pr.raw_data = {"id": 456, "title": "Test PR"}

        mock_repo.get_issues.return_value = [mock_pr]

        # Create directory structure
        pulls_dir = tmp_path / "pulls" / "closed"
        pulls_dir.mkdir(parents=True, exist_ok=True)

        # Call function
        fetch_issues.fetch_github_issues(
            tmp_path, "test/repo", "fake_token", since=None
        )

        # Verify file was written to pulls directory
        pr_file = pulls_dir / "456"
        assert pr_file.exists()

        with open(pr_file) as f:
            data = json.load(f)
            assert data == {"id": 456, "title": "Test PR"}

    @patch("fetch_issues.Github")
    @patch("common.ensure_directories")
    def test_fetch_github_issues_open_and_closed(
        self, mock_ensure_dirs, mock_github_class, tmp_path
    ):
        """Test that open and closed issues are saved to correct directories"""

        # Setup mock GitHub API
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        # Create mock open and closed issues
        mock_open_issue = MagicMock()
        mock_open_issue.number = 1
        mock_open_issue.state = "open"
        mock_open_issue.pull_request = None
        mock_open_issue.raw_data = {"id": 1, "state": "open"}

        mock_closed_issue = MagicMock()
        mock_closed_issue.number = 2
        mock_closed_issue.state = "closed"
        mock_closed_issue.pull_request = None
        mock_closed_issue.raw_data = {"id": 2, "state": "closed"}

        mock_repo.get_issues.return_value = [mock_open_issue, mock_closed_issue]

        # Create directory structure
        (tmp_path / "issues" / "open").mkdir(parents=True, exist_ok=True)
        (tmp_path / "issues" / "closed").mkdir(parents=True, exist_ok=True)

        # Call function
        fetch_issues.fetch_github_issues(
            tmp_path, "test/repo", "fake_token", since=None
        )

        # Verify files were written to correct directories
        assert (tmp_path / "issues" / "open" / "1").exists()
        assert (tmp_path / "issues" / "closed" / "2").exists()


class TestFetchGitlabIssues:
    """Tests for fetch_gitlab_issues function"""

    @patch("fetch_issues.Gitlab")
    def test_fetch_gitlab_issues(self, mock_gitlab_class, tmp_path, capsys):
        """Test fetching GitLab issues"""

        # Setup mock GitLab API
        mock_gitlab = MagicMock()
        mock_gitlab_class.return_value = mock_gitlab
        mock_project = MagicMock()
        mock_gitlab.projects.get.return_value = mock_project

        # Create mock issues
        mock_issue = MagicMock()
        mock_issue.iid = 123
        mock_issue.title = "Test GitLab Issue"
        mock_issue.state = "opened"

        mock_project.issues.list.return_value = [mock_issue]

        # Call function
        fetch_issues.fetch_gitlab_issues(
            tmp_path, "test/repo", "https://gitlab.com", "fake_token"
        )

        # Verify GitLab API calls
        mock_gitlab_class.assert_called_once_with(
            url="https://gitlab.com", private_token="fake_token"
        )
        mock_gitlab.projects.get.assert_called_once_with("test/repo")
        mock_project.issues.list.assert_called_once_with(all=True, state="opened")

        # Verify output
        captured = capsys.readouterr()
        assert "#123 - Test GitLab Issue (opened)" in captured.out


class TestParseArguments:
    """Tests for parse_arguments function"""

    def test_parse_arguments_all_required(self, tmp_path):
        """Test parsing with all required arguments"""

        args = [
            "--root-dir",
            str(tmp_path),
            "--project-url",
            "https://github.com/test/repo",
        ]

        parsed_args, parser = fetch_issues.parse_arguments(args)

        assert parsed_args.root_dir == tmp_path
        assert parsed_args.project_url == "https://github.com/test/repo"
        assert parsed_args.token is None

    def test_parse_arguments_with_token(self, tmp_path):
        """Test parsing with token argument"""

        args = [
            "--root-dir",
            str(tmp_path),
            "--project-url",
            "https://github.com/test/repo",
            "--token",
            "my_secret_token",
        ]

        parsed_args, parser = fetch_issues.parse_arguments(args)

        assert parsed_args.token == "my_secret_token"

    def test_parse_arguments_token_from_env(self, tmp_path, monkeypatch):
        """Test that token is read from API_TOKEN environment variable"""

        monkeypatch.setenv("API_TOKEN", "env_token")

        args = [
            "--root-dir",
            str(tmp_path),
            "--project-url",
            "https://github.com/test/repo",
        ]

        parsed_args, parser = fetch_issues.parse_arguments(args)

        assert parsed_args.token == "env_token"

    def test_parse_arguments_missing_required(self):
        """Test that missing required arguments raises error"""

        args = ["--root-dir", "/tmp"]

        with pytest.raises(SystemExit):
            fetch_issues.parse_arguments(args)

    def test_parse_arguments_expands_tilde(self, tmp_path):
        """Test that ~ in path is expanded"""

        args = ["--root-dir", "~/test", "--project-url", "https://github.com/test/repo"]

        parsed_args, parser = fetch_issues.parse_arguments(args)

        # Path should be expanded and absolute
        assert parsed_args.root_dir.is_absolute()
        assert "~" not in str(parsed_args.root_dir)


class TestMainExecution:
    """Tests for main execution flow"""

    @patch("fetch_issues.fetch_github_issues")
    @patch("fetch_issues.parse_arguments")
    def test_main_github_url(self, mock_parse_args, mock_fetch_github, tmp_path):
        """Test main execution with GitHub URL"""

        # Setup mock arguments
        mock_args = MagicMock()
        mock_args.root_dir = tmp_path
        mock_args.project_url = "https://github.com/owner/repo"
        mock_args.token = "test_token"
        mock_parser = MagicMock()

        mock_parse_args.return_value = (mock_args, mock_parser)

        # Execute main block code
        url_parts = fetch_issues.urlsplit(mock_args.project_url)
        host = f"{url_parts.scheme}://{url_parts.netloc}"
        repo = f"{url_parts.path}".removeprefix("/")
        pathified_repo = repo.replace("/", "_")

        assert "github" in url_parts.netloc
        assert repo == "owner/repo"
        assert pathified_repo == "owner_repo"

    @patch("fetch_issues.fetch_gitlab_issues")
    @patch("fetch_issues.parse_arguments")
    def test_main_gitlab_url(self, mock_parse_args, mock_fetch_gitlab, tmp_path):
        """Test main execution with GitLab URL"""

        # Setup mock arguments
        mock_args = MagicMock()
        mock_args.root_dir = tmp_path
        mock_args.project_url = "https://gitlab.com/owner/repo"
        mock_args.token = "test_token"
        mock_parser = MagicMock()

        mock_parse_args.return_value = (mock_args, mock_parser)

        # Execute main block code
        url_parts = fetch_issues.urlsplit(mock_args.project_url)
        host = f"{url_parts.scheme}://{url_parts.netloc}"
        repo = f"{url_parts.path}".removeprefix("/")
        pathified_repo = repo.replace("/", "_")

        assert "gitlab" in url_parts.netloc
        assert repo == "owner/repo"
        assert pathified_repo == "owner_repo"
        assert host == "https://gitlab.com"

    def test_url_parsing_with_nested_path(self):
        """Test URL parsing with nested GitLab project paths"""

        url = "https://gitlab.com/group/subgroup/project"
        url_parts = fetch_issues.urlsplit(url)
        repo = f"{url_parts.path}".removeprefix("/")
        pathified_repo = repo.replace("/", "_")

        assert repo == "group/subgroup/project"
        assert pathified_repo == "group_subgroup_project"


class TestIntegration:
    """Integration tests"""

    @patch("fetch_issues.Github")
    def test_full_github_workflow_with_decorators(self, mock_github_class, tmp_path):
        """Test complete workflow with decorators applied"""

        # Setup mock GitHub API
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        # Create mock issue
        mock_issue = MagicMock()
        mock_issue.number = 999
        mock_issue.state = "open"
        mock_issue.pull_request = None
        mock_issue.raw_data = {"id": 999, "title": "Integration test"}

        mock_repo.get_issues.return_value = [mock_issue]

        # Call the decorated function
        fetch_issues.fetch_github_issues(tmp_path, "test/repo", "token")

        # Verify directories were created
        assert (tmp_path / "issues" / "open").exists()
        assert (tmp_path / "issues" / "closed").exists()
        assert (tmp_path / "pulls" / "open").exists()
        assert (tmp_path / "pulls" / "closed").exists()

        # Verify issue was saved
        issue_file = tmp_path / "issues" / "open" / "999"
        assert issue_file.exists()

        # Verify last_updated file was created
        last_updated_file = tmp_path / "last_updated"
        assert last_updated_file.exists()
