from unittest.mock import patch

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
