from unittest.mock import MagicMock, patch

from model.model import Model
from model.objects.atom import Atom
from model.objects.network import Network
from parser.parser import Parser


def _parser_with_apps(applications):
    p = Parser(test=True)
    p._blueprint = {"applications": list(applications)}
    return p


def test_sync_inserts_gateway_and_creates_atoms():
    p = _parser_with_apps(
        [{"name": "web", "image": "nginx:latest", "replicas": 2}]
    )
    Model(p).sync()
    assert p.applications[0]["name"] == "TINYOPS_GATEWAY"
    assert len(Atom.get_atoms_by_name("TINYOPS_GATEWAY")) == 1
    assert len(Atom.get_atoms_by_name("web")) == 2


def test_sync_creates_network_when_application_has_network():
    p = _parser_with_apps(
        [
            {
                "name": "svc",
                "image": "nginx:latest",
                "replicas": 1,
                "network": "app_net",
            }
        ]
    )
    Model(p).sync()
    assert Network.get_by_name("app_net") is not None
    assert Network.get_by_name("tinyops_network") is not None


def test_is_replica_more_than_ports():
    m = Model(_parser_with_apps([]))
    assert m._is_replica_more_than_ports({"replicas": 2, "ports": {"80": 80}})
    assert not m._is_replica_more_than_ports({"replicas": 1, "ports": {"80": 80}})
    assert not m._is_replica_more_than_ports({"replicas": 5})


def test_sync_skips_app_when_replicas_exceed_one_with_ports():
    p = _parser_with_apps(
        [
            {
                "name": "bad",
                "image": "nginx:latest",
                "replicas": 2,
                "ports": {"80": 8080},
            }
        ]
    )
    Model(p).sync()
    assert Atom.get_atoms_by_name("bad") == []


def test_sync_marks_extra_replicas_for_deletion():
    p = _parser_with_apps([{"name": "web", "image": "nginx:latest", "replicas": 2}])
    Model(p).sync()
    p._blueprint = {
        "applications": [{"name": "web", "image": "nginx:latest", "replicas": 1}],
    }
    Model(p).sync()
    marked = [a for a in Atom.get_atoms_by_name("web") if a.up_for_deletion]
    assert len(marked) == 1


def test_sync_marks_atom_not_in_blueprint_for_deletion():
    p = _parser_with_apps([{"name": "web", "image": "nginx:latest", "replicas": 1}])
    Model(p).sync()
    orphan = Atom(name="orphan", image="nginx:latest")
    orphan.up_for_creation = False
    Model(p).sync()
    assert orphan.up_for_deletion


def test_sync_marks_network_unused_for_deletion():
    p = _parser_with_apps(
        [
            {
                "name": "a",
                "image": "nginx:latest",
                "replicas": 1,
                "network": "n1",
            }
        ]
    )
    Model(p).sync()
    n1 = Network.get_by_name("n1")
    p._blueprint = {
        "applications": [{"name": "b", "image": "nginx:latest", "replicas": 1}],
    }
    Model(p).sync()
    assert n1.up_for_deletion


def test_delete_config_changed_atoms_env_mismatch():
    p = _parser_with_apps([{"name": "web", "image": "nginx:latest", "replicas": 1, "env": {"K": "1"}}])
    Model(p).sync()
    web = Atom.get_atoms_by_name("web")[0]
    web.up_for_deletion = False
    p._blueprint = {
        "applications": [
            {"name": "web", "image": "nginx:latest", "replicas": 1, "env": {"K": "2"}},
        ],
    }
    Model(p).sync()
    assert web.up_for_deletion


def test_update_config_changed_atoms_domain_and_ssl():
    p = _parser_with_apps(
        [
            {
                "name": "web",
                "image": "nginx:latest",
                "replicas": 1,
                "domain": "a.example",
                "ssl": False,
            }
        ]
    )
    Model(p).sync()
    web = Atom.get_atoms_by_name("web")[0]
    web.up_for_deletion = False
    p._blueprint = {
        "applications": [
            {
                "name": "web",
                "image": "nginx:latest",
                "replicas": 1,
                "domain": "b.example",
                "ssl": True,
            },
        ],
    }
    Model(p).sync()
    assert web.domain == "b.example"
    assert web.ssl is True


def test_get_active_atoms_by_name_excludes_marked_for_deletion():
    p = _parser_with_apps([])
    m = Model(p)
    a = Atom(name="x", image="nginx:latest")
    a.up_for_deletion = True
    b = Atom(name="x", image="nginx:latest")
    b.up_for_deletion = False
    assert m._get_active_atoms_by_name("x") == [b]


@patch("model.objects.atom.db")
@patch("model.model.db")
def test_add_git_repository_to_db_appends_repo(mock_model_db, mock_atom_db):
    p = _parser_with_apps(
        [
            {
                "name": "gitapp",
                "git": {"url": "git@github.com:org/repo.git", "branch": "main"},
                "replicas": 1,
            }
        ]
    )
    mock_atom_db.get.return_value = "built:latest"
    Model(p).sync()
    mock_model_db.append_to_list_if_not_exists.assert_called()
    atom = Atom.get_atoms_by_name("gitapp")[0]
    assert atom.git["repo_name"] == "repo-main"
    assert atom.ready_for_creation is True
    assert atom.image == "built:latest"


@patch("model.model.db")
def test_delete_config_changed_when_linked_git_image_differs(mock_db):
    git_spec = {
        "name": "gitapp",
        "git": {"url": "git@github.com:org/repo.git", "branch": "main"},
        "replicas": 1,
    }
    p = _parser_with_apps([git_spec])
    mock_db.get.return_value = "img:1"
    Model(p).sync()
    atom = Atom.get_atoms_by_name("gitapp")[0]
    atom.image = "img:1"
    atom.link = MagicMock()
    atom.up_for_deletion = False
    p._blueprint = {"applications": [git_spec]}
    mock_db.get.return_value = "img:2"
    Model(p).sync()
    assert atom.up_for_deletion
