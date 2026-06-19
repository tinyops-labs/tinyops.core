from unittest.mock import MagicMock, patch

import pytest

from model.api_service import ApiService
from parser.blueprint_validator import BlueprintValidationError


def _model():
    m = MagicMock()
    m.atoms = []
    m.networks = []
    m._parser = MagicMock()
    m._parser.blueprint = {"applications": []}
    return m


def test_get_current_state_structure():
    m = _model()
    with patch("model.api_service.Utils.get_system_stats", return_value={"cpu": 1}):
        s = ApiService(m).get_current_state()
    assert "atoms" in s and "networks" in s and "blueprint" in s
    assert s["system_stats"] == {"cpu": 1}


def test_get_container_logs_gateway():
    m = _model()
    gw = MagicMock()
    gw.get_container_logs.return_value = ["line"]
    with patch("model.api_service.Atom.get_gateway_atom", return_value=gw):
        out = ApiService(m).get_container_logs_by_id("TINYOPS_GATEWAY")
    assert out == ["line"]


def test_get_container_logs_by_atom_id():
    m = _model()
    atom = MagicMock()
    atom.get_container_logs.return_value = ["a"]
    with patch("model.api_service.Atom.get_by_id", return_value=atom):
        out = ApiService(m).get_container_logs_by_id("some-id")
    assert out == ["a"]


def test_get_blueprint_delegates_to_parser():
    m = _model()
    m._parser._load_blueprint_from_local.return_value = {"applications": [{"name": "x"}]}
    assert ApiService(m).get_blueprint()["applications"][0]["name"] == "x"


def test_update_blueprint_validation_error():
    m = _model()
    bad = {"applications": [{}]}
    with pytest.raises(BlueprintValidationError) as ei:
        ApiService(m).update_blueprint(bad)
    assert ei.value.errors
    m._parser.update_blueprint_file.assert_not_called()


def test_update_blueprint_success():
    m = _model()
    good = {"applications": [{"name": "a", "image": "nginx"}]}
    assert ApiService(m).update_blueprint(good) is True
    m._parser.update_blueprint_file.assert_called_once_with(good)


@patch("model.api_service.SSHWorker")
def test_get_ssh_public_key(mock_ssh):
    mock_ssh.return_value.retrieve_public_key.return_value = "ssh-rsa AAA"
    m = _model()
    assert ApiService(m).get_ssh_public_key() == "ssh-rsa AAA"
