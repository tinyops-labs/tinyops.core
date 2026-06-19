import shelve

from persistence.tinyops_db import TinyOpsDB


def test_set_get_two_part_key(tmp_path):
    t = object.__new__(TinyOpsDB)
    t.db = shelve.open(str(tmp_path / "s"), "c")
    try:
        t.set("a", "b", value=3)
        assert t.get("a", "b") == 3
    finally:
        t.db.close()


def test_get_single_key(tmp_path):
    t = object.__new__(TinyOpsDB)
    t.db = shelve.open(str(tmp_path / "s2"), "c")
    try:
        t.set("only", value=[1, 2])
        assert t.get("only") == [1, 2]
    finally:
        t.db.close()


def test_get_list_creates_empty(tmp_path):
    t = object.__new__(TinyOpsDB)
    t.db = shelve.open(str(tmp_path / "s3"), "c")
    try:
        lst = t.get_list("pipelines")
        assert lst == []
        assert t.get("pipelines") == []
    finally:
        t.db.close()


def test_append_to_list_if_not_exists(tmp_path):
    t = object.__new__(TinyOpsDB)
    t.db = shelve.open(str(tmp_path / "s4"), "c")
    try:
        t.append_to_list_if_not_exists("repos", {"id": 1})
        t.append_to_list_if_not_exists("repos", {"id": 1})
        assert len(t.get_list("repos")) == 1
    finally:
        t.db.close()


def test_remove_from_list(tmp_path):
    t = object.__new__(TinyOpsDB)
    t.db = shelve.open(str(tmp_path / "s5"), "c")
    try:
        t.append_to_list("items", "a")
        t.append_to_list("items", "b")
        t.remove_from_list("items", "a")
        assert t.get_list("items") == ["b"]
    finally:
        t.db.close()
