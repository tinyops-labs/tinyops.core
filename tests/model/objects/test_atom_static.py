from unittest.mock import MagicMock

from model.objects.atom import Atom


def test_get_gateway_atom():
    Atom.atoms = []
    g = Atom(name="TINYOPS_GATEWAY", image="gw")
    Atom(name="a", image="i")
    assert Atom.get_gateway_atom() is g


def test_get_git_urls_dedupes():
    Atom.atoms = []
    a = Atom(name="a", image="i", git={"url": "https://x.git", "branch": "m"})
    Atom(name="b", image="j", git={"url": "https://x.git", "branch": "m"})
    assert Atom.get_git_urls() == ["https://x.git"]


def test_get_domains_dedupes_by_domain():
    Atom.atoms = []
    Atom(name="a", image="i", domain="d.example", ssl=True)
    Atom(name="b", image="j", domain="d.example", ssl=False)
    d = Atom.get_domains()
    assert len(d) == 1
    assert d[0]["domain"] == "d.example"


def test_get_ssl_domains():
    Atom.atoms = []
    Atom(name="a", image="i", domain="s.example", ssl=True)
    Atom(name="b", image="j", domain="s.example", ssl=False)
    assert Atom.get_ssl_domains() == ["s.example"]


def test_atom_dict_with_link():
    Atom.atoms = []
    a = Atom(name="n", image="img")
    link = MagicMock()
    link.name = "cname"
    link.attrs = {"Created": "t"}
    link.logs.return_value = b""
    a.link = link
    d = a.__dict__()
    assert d["link"] is True
    assert d["container"]["name"] == "cname"
