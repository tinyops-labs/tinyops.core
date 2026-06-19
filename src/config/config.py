import os

from utils.utils import Utils
from persistence.tinyops_db import db
from utils.logger import info

class Config:

    def __init__(self):
        self.gitops_url = "local"
        self._set_auth_key()

    def _set_auth_key(self):
        key = os.getenv("AUTH_KEY") or Utils.generate_random_string(32)
        db.set("auth_key", value=key)
        info(f"Auth key set to {key}")

    @property
    def auth_key(self):
        return db.get("auth_key")


config = Config()
