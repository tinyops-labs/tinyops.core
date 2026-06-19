from unittest.mock import MagicMock, patch

import docker
import pytest

from controller.controller import Controller
from docker.errors import ImageNotFound
from model.model import Model
from model.objects.atom import Atom
from model.objects.network import Network
from parser.parser import Parser


def _parser(apps):
    p = Parser(test=True)
    p._blueprint = {"applications": list(apps)}
    return p


def _controller(model, client):
    with patch("controller.controller.docker.from_env", return_value=client):
        return Controller(model)


def test_get_docker_client_raises_when_docker_unavailable():
    m = Model(_parser([]))
    with patch("controller.controller.docker.from_env", side_effect=RuntimeError("down")):
        with pytest.raises(Exception, match="Could not connect to Docker"):
            Controller(m)


def test_pull_image_if_it_doesnt_exist_locally_when_present():
    m = Model(_parser([]))
    client = MagicMock()
    c = _controller(m, client)
    c._pull_image_if_it_doesnt_exist_locally("nginx:latest")
    client.images.get.assert_called_once_with("nginx:latest")
    client.images.pull.assert_not_called()


def test_pull_image_if_it_doesnt_exist_locally_pulls_when_missing():
    m = Model(_parser([]))
    client = MagicMock()
    client.images.get.side_effect = ImageNotFound("x")
    c = _controller(m, client)
    c._pull_image_if_it_doesnt_exist_locally("nginx:latest")
    client.images.pull.assert_called_once_with("nginx:latest")


def test_link_docker_containers_to_atoms_links_matching_container():
    m = Model(_parser([]))
    client = MagicMock()
    client.containers.list.return_value = []
    c = _controller(m, client)
    atom = Atom(name="web", image="nginx:latest")
    atom.up_for_creation = False
    container_id = "cid-from-docker"
    atom.id = "stale-id"
    dc = MagicMock()
    dc.labels = {
        "tinyops_container_id": container_id,
        "tinyops_name": "web",
        "tinyops_image": "nginx:latest",
    }
    client.containers.list.return_value = [dc]
    c._link_docker_containers_to_atoms()
    assert atom.link is dc
    assert atom.id == container_id
    assert atom.up_for_creation is False


def test_link_docker_containers_skips_when_id_already_linked_elsewhere():
    m = Model(_parser([]))
    client = MagicMock()
    c = _controller(m, client)
    a1 = Atom(name="web", image="nginx:latest")
    a1.up_for_creation = False
    a2 = Atom(name="web", image="nginx:latest")
    a2.up_for_creation = False
    dc = MagicMock()
    dc.labels = {
        "tinyops_container_id": a1.id,
        "tinyops_name": "web",
        "tinyops_image": "nginx:latest",
    }
    a1.link = dc
    client.containers.list.return_value = [dc]
    c._link_docker_containers_to_atoms()
    assert a2.link is None


def test_delete_unused_docker_containers_removes_orphan():
    m = Model(_parser([]))
    client = MagicMock()
    c = _controller(m, client)
    orphan = MagicMock()
    orphan.labels = {"tinyops_container_id": "no-such-atom"}
    client.containers.list.return_value = [orphan]
    c._delete_unused_docker_containers()
    orphan.remove.assert_called_once_with(force=True)


def test_delete_docker_containers_up_for_deletion_removes_container_and_atom():
    m = Model(_parser([]))
    client = MagicMock()
    c = _controller(m, client)
    atom = Atom(name="gone", image="nginx:latest")
    link = MagicMock()
    atom.link = link
    atom.up_for_deletion = True
    before = len(Atom.atoms)
    c._delete_docker_containers_up_for_deletion()
    link.remove.assert_called_once_with(force=True)
    assert atom not in Atom.atoms
    assert len(Atom.atoms) == before - 1


def test_create_docker_containers_up_for_creation():
    m = Model(_parser([]))
    client = MagicMock()
    client.containers.list.return_value = []
    created = MagicMock()
    client.containers.create.return_value = created
    tinyops_net = MagicMock()
    client.networks.get.return_value = tinyops_net
    c = _controller(m, client)
    atom = Atom(
        name="app",
        image="nginx:latest",
        env={"K": "v"},
        ports={"8080": 80},
        volumes=["/host:/ctr"],
    )
    atom.up_for_creation = True
    c._create_docker_containers_up_for_creation()
    client.images.get.assert_called_once_with("nginx:latest")
    client.containers.create.assert_called_once()
    kwargs = client.containers.create.call_args.kwargs
    assert kwargs["image"] == "nginx:latest"
    assert kwargs["environment"] == {"K": "v"}
    assert kwargs["ports"] == {"8080/tcp": 80}
    assert "/host" in kwargs["volumes"]
    assert kwargs["labels"]["tinyops_name"] == "app"
    tinyops_net.connect.assert_called_once_with(created, aliases=["app"])
    assert atom.link is created
    assert atom.up_for_creation is False
    created.start.assert_called_once()


def test_create_docker_networks_up_for_creation():
    m = Model(_parser([]))
    client = MagicMock()
    client.networks.list.return_value = []
    c = _controller(m, client)
    n = Network("custom_net")
    n.up_for_creation = True
    c._create_docker_networks_up_for_creation()
    client.networks.create.assert_called_once()
    kw = client.networks.create.call_args.kwargs
    assert kw["name"] == "custom_net"
    assert kw["labels"]["tinyops_id"] == n.id


def test_create_docker_networks_skips_when_exists():
    m = Model(_parser([]))
    client = MagicMock()
    existing = MagicMock()
    existing.name = "custom_net"
    client.networks.list.return_value = [existing]
    c = _controller(m, client)
    Network("custom_net")
    c._create_docker_networks_up_for_creation()
    client.networks.create.assert_not_called()


def test_remove_networks_up_for_deletion():
    m = Model(_parser([]))
    client = MagicMock()
    dn = MagicMock()
    dn.name = "gone_net"
    client.networks.list.return_value = [dn]
    c = _controller(m, client)
    with patch.object(c, "_get_docker_network_by_name", return_value=dn):
        n = Network("gone_net")
        n.up_for_deletion = True
        c._remove_networks_up_for_deletion()
    dn.remove.assert_called_once()
    assert n not in Network.networks


def test_remove_unused_networks():
    m = Model(_parser([]))
    client = MagicMock()
    dn = MagicMock()
    dn.name = "orphan_net"
    dn.attrs = {"Labels": {"tinyops_id": "x"}}
    client.networks.list.return_value = [dn]
    c = _controller(m, client)
    with patch.object(c, "_remove_network") as rm:
        c._remove_unused_networks()
    rm.assert_called_once_with(dn)


def test_remove_network_skips_tinyops_network():
    m = Model(_parser([]))
    client = MagicMock()
    c = _controller(m, client)
    net = MagicMock()
    net.name = "tinyops_network"
    c._remove_network(net)
    net.remove.assert_not_called()


def test_remove_network_removes_non_tinyops():
    m = Model(_parser([]))
    client = MagicMock()
    c = _controller(m, client)
    net = MagicMock()
    net.name = "other"
    c._remove_network(net)
    net.remove.assert_called_once()


def test_recreate_illegally_removed_marks_atom_when_container_gone():
    m = Model(_parser([]))
    client = MagicMock()
    c = _controller(m, client)
    atom = Atom(name="web", image="nginx:latest")
    link = MagicMock()
    link.reload.side_effect = docker.errors.NotFound("missing")
    atom.link = link
    atom.up_for_creation = False
    c._recreate_illegally_removed_docker_containers()
    assert atom.up_for_creation is True


def test_recreate_illegally_removed_starts_when_not_running():
    m = Model(_parser([]))
    client = MagicMock()
    c = _controller(m, client)
    atom = Atom(name="web", image="nginx:latest")
    link = MagicMock()
    link.status = "exited"
    atom.link = link
    with patch.object(c, "_start_container") as st:
        c._recreate_illegally_removed_docker_containers()
    st.assert_called_once_with(link)


def test_start_container_swallows_start_errors():
    m = Model(_parser([]))
    client = MagicMock()
    c = _controller(m, client)
    ctr = MagicMock()
    ctr.name = "n"
    ctr.start.side_effect = RuntimeError("fail")
    c._start_container(ctr)


def test_iterate_calls_model_sync():
    p = _parser([{"name": "w", "image": "nginx:latest", "replicas": 1}])
    m = Model(p)
    client = MagicMock()
    client.containers.list.return_value = []
    client.networks.list.return_value = []
    c = _controller(m, client)
    with patch.object(m, "sync") as sm, patch.object(
        c, "_link_docker_containers_to_atoms"
    ), patch.object(
        c, "_delete_unused_docker_containers"
    ), patch.object(
        c, "_create_docker_networks_up_for_creation"
    ), patch.object(
        c, "_delete_docker_containers_up_for_deletion"
    ), patch.object(
        c, "_create_docker_containers_up_for_creation"
    ), patch.object(
        c, "_recreate_illegally_removed_docker_containers"
    ), patch.object(
        c, "_remove_unused_networks"
    ), patch.object(
        c, "_remove_networks_up_for_deletion"
    ), patch.object(
        c, "_create_ssl_certificates"
    ), patch.object(
        c, "update_gateway_configuration"
    ):
        c._iterate()
    sm.assert_called_once()


@patch("controller.controller.db")
@patch.object(Controller, "update_gateway_configuration")
def test_create_ssl_certificates_triggers_cert_when_pending(mock_update_gw, mock_db):
    mock_db.get.side_effect = lambda d, k: None
    p = _parser(
        [
            {
                "name": "svc",
                "image": "g:latest",
                "replicas": 1,
                "domain": "app.example",
                "ssl": True,
            }
        ]
    )
    m = Model(p)
    m.sync()
    gw = Atom.get_gateway_atom()
    glink = MagicMock()
    gw.link = glink
    for a in Atom.atoms:
        if a.name == "svc":
            a.link = MagicMock()
    client = MagicMock()
    client.containers.list.return_value = []
    client.networks.list.return_value = []
    c = _controller(m, client)
    with patch.object(c._gateway_manager, "create_ssl_certificate") as cert:
        c._create_ssl_certificates()
    cert.assert_called_once_with("app.example", glink)
    mock_db.set.assert_any_call("app.example", "ssl_pending", True)
    mock_db.set.assert_any_call("app.example", "ssl_pending", False)


@patch("controller.controller.db")
@patch.object(Controller, "update_gateway_configuration")
def test_create_ssl_certificates_skips_when_already_ready_or_failed(
    mock_update_gw, mock_db
):
    def getter(domain, key):
        if key == "ssl_ready" and domain == "d.example":
            return True
        return None

    mock_db.get.side_effect = getter
    p = _parser([])
    m = Model(p)
    atom = Atom(name="a", image="nginx:latest", domain="d.example", ssl=True)
    atom.link = MagicMock()
    atom.up_for_creation = False
    client = MagicMock()
    c = _controller(m, client)
    with patch.object(c._gateway_manager, "create_ssl_certificate") as cert:
        c._create_ssl_certificates()
    cert.assert_not_called()


@patch("controller.controller.db")
@patch.object(Controller, "update_gateway_configuration")
def test_create_ssl_certificates_skips_when_ssl_creation_failed(
    mock_update_gw, mock_db
):
    def getter(domain, key):
        if key == "ssl_creation_failed":
            return True
        return None

    mock_db.get.side_effect = getter
    m = Model(_parser([]))
    atom = Atom(name="a", image="nginx:latest", domain="e.example", ssl=True)
    atom.link = MagicMock()
    atom.up_for_creation = False
    client = MagicMock()
    c = _controller(m, client)
    with patch.object(c._gateway_manager, "create_ssl_certificate") as cert:
        c._create_ssl_certificates()
    cert.assert_not_called()
