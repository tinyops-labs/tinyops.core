from model.objects.network import Network


def test_get_by_name():
    Network.networks = []
    n = Network("net-a")
    assert Network.get_by_name("net-a") is n
    assert Network.get_by_name("missing") is None
