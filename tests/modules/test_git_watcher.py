from unittest.mock import patch, MagicMock

from modules.git_watcher import GitWatcher


@patch("modules.git_watcher.Atom.get_git_urls", return_value=["https://keep.git"])
@patch("modules.git_watcher.db")
def test_update_repos_list_removes_unused(mock_db, _):
    mock_db.get_list.return_value = [
        {"url": "https://keep.git", "branch": "main", "repo_name": "a-main"},
        {"url": "https://orphan.git", "branch": "main", "repo_name": "o-main"},
    ]
    gw = GitWatcher()
    gw._update_repos_list()
    mock_db.set.assert_called_once()
    kw = mock_db.set.call_args.kwargs
    assert kw["value"] == [
        {"url": "https://keep.git", "branch": "main", "repo_name": "a-main"},
    ]


@patch("modules.git_watcher.Utils.generate_random_string", return_value="pipe-id")
@patch("modules.git_watcher.db")
def test_check_skips_when_remote_unchanged(mock_db, _):
    mock_db.get.return_value = "abc123"
    gw = GitWatcher()
    gw.repos = [{"url": "git@x/y.git", "branch": "main", "repo_name": "y-main"}]
    with patch.object(gw, "_get_remote_revision", return_value="abc123") as remote:
        with patch.object(gw, "_pull_repository") as pull:
            gw._check_if_new_revision_available()
    remote.assert_called_once_with("git@x/y.git", "main")
    pull.assert_not_called()
    mock_db.append_to_list.assert_not_called()


@patch("modules.git_watcher.Utils.generate_random_string", return_value="pipe-id")
@patch("modules.git_watcher.db")
def test_check_pulls_and_creates_pipeline_when_remote_changed(mock_db, _):
    mock_db.get.return_value = "oldsha"
    gw = GitWatcher()
    gw.repos = [{"url": "git@x/y.git", "branch": "main", "repo_name": "y-main"}]
    with patch.object(gw, "_get_remote_revision", return_value="newsha"):
        with patch.object(gw, "_pull_repository", return_value=True) as pull:
            gw._check_if_new_revision_available()
    pull.assert_called_once_with("y-main")
    mock_db.set.assert_called_once_with("y-main", "revision", "newsha")
    mock_db.append_to_list.assert_called_once()
    args = mock_db.append_to_list.call_args.args
    assert args[0] == "pipelines"
    assert args[1]["repo_name"] == "y-main"
    assert args[1]["image_name"] == "y-main-newsha"
    assert args[1]["status"] == "pending"


@patch("modules.git_watcher.db")
def test_check_skips_when_ls_remote_fails(mock_db):
    gw = GitWatcher()
    gw.repos = [{"url": "git@x/y.git", "branch": "main", "repo_name": "y-main"}]
    with patch.object(gw, "_get_remote_revision", return_value=None):
        with patch.object(gw, "_pull_repository") as pull:
            gw._check_if_new_revision_available()
    pull.assert_not_called()
    mock_db.append_to_list.assert_not_called()


@patch("modules.git_watcher.subprocess.run")
@patch("modules.git_watcher.db")
def test_get_remote_revision_parses_sha(mock_db, mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="deadbeef0123456789abcdef0123456789abcdef\trefs/heads/main\n",
        stderr="",
    )
    gw = GitWatcher()
    sha = gw._get_remote_revision("git@x/y.git", "main")
    assert sha == "deadbeef0123456789abcdef0123456789abcdef"
    mock_run.assert_called_once()
    assert mock_run.call_args.args[0] == ["git", "ls-remote", "git@x/y.git", "refs/heads/main"]


@patch("modules.git_watcher.subprocess.run")
@patch("modules.git_watcher.db")
def test_get_remote_revision_returns_none_on_failure(mock_db, mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="denied")
    gw = GitWatcher()
    assert gw._get_remote_revision("git@x/y.git", "main") is None
