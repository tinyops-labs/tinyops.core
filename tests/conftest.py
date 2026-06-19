import pytest

from model.objects.atom import Atom
from model.objects.network import Network


@pytest.fixture(autouse=True)
def _clear_model_objects():
    Atom.atoms = []
    Network.networks = []
    yield
    Atom.atoms = []
    Network.networks = []
