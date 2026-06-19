from unittest.mock import patch

from config.config import Config


def test_auth_key_reads_from_db():
    with patch("config.config.db") as dbm:
        dbm.get.return_value = "k9"
        with patch.object(Config, "_set_auth_key", lambda self: None):
            c = Config()
        assert c.auth_key == "k9"
