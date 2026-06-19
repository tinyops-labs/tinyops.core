from modules.ssh_worker import SSHWorker


def test_retrieve_public_key_reads_file(tmp_path):
    w = SSHWorker()
    w.base_dir = tmp_path / "ssh"
    w.private_key_path = w.base_dir / "id_rsa"
    w.public_key_path = w.private_key_path.with_suffix(".pub")
    w.base_dir.mkdir(parents=True, exist_ok=True)
    w.public_key_path.write_text("ssh-rsa DATA", encoding="utf-8")
    assert w.retrieve_public_key() == "ssh-rsa DATA"
