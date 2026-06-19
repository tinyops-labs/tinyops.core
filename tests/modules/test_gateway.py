from unittest.mock import MagicMock, patch

from model.objects.atom import Atom
from modules.gateway import Gateway


def test_get_applications_skips_gateway_and_unlinked():
    Atom.atoms = []
    gw = Atom(name="TINYOPS_GATEWAY", image="g")
    gw.link = MagicMock()
    a = Atom(name="app", image="nginx")
    a.link = None
    b = Atom(name="svc", image="nginx")
    b.link = MagicMock()
    b.link.name = "c1"
    apps = Gateway().get_applications()
    assert "TINYOPS_GATEWAY" not in apps
    assert "app" not in apps
    assert "svc" in apps
    assert apps["svc"]["upstreams"][0]["atom_name"] == "c1"


@patch("modules.gateway.db")
def test_get_applications_uses_first_port(mock_db):
    Atom.atoms = []
    mock_db.get.return_value = None
    b = Atom(name="svc", image="nginx", ports={"8080": 80})
    b.link = MagicMock()
    b.link.name = "x"
    apps = Gateway().get_applications()
    assert apps["svc"]["upstreams"][0]["atom_port"] == "8080"


def test_fallback_config_non_empty():
    g = Gateway()
    assert "listen 80" in g._fallback_config()


def test_update_config_writes_when_hash_changes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    g = Gateway()
    g.config_path = str(tmp_path / "cfg")
    import os

    os.makedirs(g.config_path, exist_ok=True)
    g.config_hash = None
    with patch.object(Gateway, "generate_config", return_value="nginx {}"):
        assert g.update_config() is True
    with patch.object(Gateway, "generate_config", return_value="nginx {}"):
        assert g.update_config() is False


def test_reload_nginx_calls_exec():
    g = Gateway()
    atom = MagicMock()
    atom.link.exec_run.return_value = MagicMock(exit_code=0)
    g.reload_nginx(atom)
    atom.link.exec_run.assert_called_once()


def test_create_ssl_success_sets_db():
    g = Gateway()
    ctr = MagicMock()
    ctr.exec_run.return_value = (0, b"ok")
    with patch("modules.gateway.db") as dbm:
        g.create_ssl_certificate("d.example", ctr)
    dbm.set.assert_any_call("d.example", "ssl_ready", True)


def test_create_ssl_failure_sets_db():
    g = Gateway()
    ctr = MagicMock()
    ctr.exec_run.return_value = (1, b"err")
    with patch("modules.gateway.db") as dbm:
        g.create_ssl_certificate("d.example", ctr)
    dbm.set.assert_any_call("d.example", "ssl_creation_failed", True)
