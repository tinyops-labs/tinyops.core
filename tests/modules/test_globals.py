from modules.globals import Global


def test_global_sync_default():
    assert Global.sync is True
