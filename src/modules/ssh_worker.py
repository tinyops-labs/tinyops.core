import os
import subprocess
import pathlib
from utils.logger import info


class SSHWorker:

    def __init__(self):
        self.base_dir = pathlib.Path(os.path.expanduser("~")) / ".tinyops" / "ssh"
        self.private_key_path = self.base_dir / "id_rsa"
        self.public_key_path = self.private_key_path.with_suffix(".pub")

    def create_ssh_pair_if_not_exist(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.base_dir.chmod(0o700)

        if not self.private_key_path.exists():
            info("Creating SSH pair...")
            subprocess.run([
                "ssh-keygen",
                "-t", "rsa",
                "-b", "4096",
                "-f", self.private_key_path,
                "-N", "",
                "-C", "TinyOps"
            ], check=True)

            self.private_key_path.chmod(0o600)
            self.public_key_path.chmod(0o644)

            info("SSH pair created successfully.")
        else:
            info("SSH pair already exists.")

        info(f"Public key: {self.retrieve_public_key()}")

    def retrieve_public_key(self):
        with self.public_key_path.open("r") as f:
            return f.read()
