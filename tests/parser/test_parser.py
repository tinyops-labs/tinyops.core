from unittest.mock import mock_open, patch

import yaml

from parser.parser import Parser


def test_applications_default_empty():
    p = Parser(test=True)
    assert p.applications == []


def test_add_to_blueprint_appends():
    p = Parser(test=True)
    p._blueprint = {"applications": [{"name": "a", "image": "i"}]}
    p.add_to_blueprint({"name": "b", "image": "j"})
    assert len(p.applications) == 2
    assert p.applications[-1]["name"] == "b"


def test_load_blueprint_test_mode_does_not_replace():
    p = Parser(test=True)
    p._blueprint = {"applications": [{"name": "x", "image": "y"}]}
    with patch.object(Parser, "_load_blueprint_from_local", return_value={"applications": []}):
        p.load_blueprint()
    assert p.applications[0]["name"] == "x"


def test_load_blueprint_non_test_replaces():
    p = Parser(test=False)
    with patch("parser.parser.config") as cfg:
        cfg.gitops_url = "local"
        with patch.object(
            Parser, "_load_blueprint_from_local", return_value={"applications": [{"name": "z", "image": "i"}]}
        ):
            p.load_blueprint()
    assert p.applications[0]["name"] == "z"


def test_load_blueprint_from_git_repo():
    p = Parser(test=False)
    with patch("parser.parser.config") as cfg:
        cfg.gitops_url = "remote"
        p.load_blueprint()
    assert p.applications == []


def test_update_blueprint_file_writes_yaml(tmp_path, monkeypatch):
    p = Parser(test=True)
    target = tmp_path / "blueprint.yaml"
    monkeypatch.chdir(tmp_path)

    data = {
        "applications": [
            {"name": "n1", "image": "i1"},
            {"name": "n2", "image": "i2"},
        ]
    }
    with patch("builtins.open", mock_open()) as m:
        p.update_blueprint_file(data)
    handle = m()
    written = "".join(call.args[0] for call in handle.write.call_args_list if call.args)
    parsed = yaml.safe_load(written)
    assert parsed["applications"][0]["name"] == "n1"
    assert parsed["applications"][1]["name"] == "n2"
