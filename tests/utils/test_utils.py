from utils.utils import DotDict, Utils


def test_generate_random_string_length():
    assert len(Utils.generate_random_string(8)) == 8


def test_extract_repo_name_ssh_url():
    assert (
        Utils.extract_repo_name_from_git_url_and_branch(
            "git@github.com:org/repo.git", "feature/x"
        )
        == "repo-feature-x"
    )


def test_extract_repo_name_https():
    assert (
        Utils.extract_repo_name_from_git_url_and_branch(
            "https://github.com/org/foo.git", "main"
        )
        == "foo-main"
    )


def test_dotdict_nested_attr():
    d = DotDict({"a": {"b": 1}})
    assert d.a.b == 1


def test_dotdict_top_level():
    d = DotDict({"x": 2})
    assert d.x == 2
